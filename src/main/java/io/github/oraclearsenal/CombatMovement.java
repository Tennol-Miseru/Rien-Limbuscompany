package io.github.oraclearsenal;

import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.network.chat.Component;

/**
 * Short, real-world, server-owned combat steps. A move is swept one tick at a
 * time, never an instant replacement for a weapon's hit range or Furioso blink.
 * Every step checks the swept hitbox and supporting floor before moving.
 */
public final class CombatMovement {
    private static final Map<UUID, Motion> ACTIVE = new HashMap<>();
    private static final Set<UUID> DEBUG = new HashSet<>();

    public static boolean toggleDebug(ServerPlayer player) {
        if (!DEBUG.add(player.getUUID())) { DEBUG.remove(player.getUUID()); return false; }
        return true;
    }

    private static final Map<UUID, Long> ORDINARY_START = new HashMap<>();
    private static final int ORDINARY_INTERVAL = 8;
    private static final double MAX_TICK_STEP = 0.50;
    private static final double EPSILON = 0.00001;

    private CombatMovement() { }

    /** A normal left-click only advances the player for the knight lance.
     * The giant scythe makes one ordinary swipe without server-forced movement;
     * its target-crossing movement is exclusive to Furioso skills. */
    public static boolean ordinary(ServerPlayer player, ItemStack staff, long now) {
        if (!(staff.getItem() instanceof OracleWeaponItem)
                || OracleWeaponItem.getForm(staff) == 0 || !eligible(player, true)
                || OracleCombat.isFinisherActive(player.getUUID())) return false;
        long previous = ORDINARY_START.getOrDefault(player.getUUID(), Long.MIN_VALUE / 2);
        // Heart speeds up nine-form swings as well as vanilla attack speed.
        int interval = player.hasEffect(HeartEffect.HEART) ? 7 : ORDINARY_INTERVAL;
        if (now - previous < interval) return false;
        if (player.getAttackStrengthScale(0.5f) < 0.65f) return false;
        ORDINARY_START.put(player.getUUID(), now);
        OracleWeaponItem.recordUse(staff, now);
        OracleWeaponItem.setAnimation(staff, 3, now);
        int form = Math.max(1, Math.min(9, OracleWeaponItem.getForm(staff)));
        if (form == 7 && supportedFloor(player))
            begin(player, staff, form, false, false, now, null);
        return true;
    }

    /** A special beat begins AFTER the existing morph/teleport, using that landing direction. */
    public static void special(ServerPlayer player, ItemStack staff, int form,
                               boolean cinematic, long now, Vec3 targetPosition) {
        begin(player, staff, form, true, cinematic, now, targetPosition);
    }

    /**
     * V-key opening: a brief, collision-checked real run-up before the first blink.
     * The actor first lowers into the reference crouch and covers the face;
     * ticks 7-11 then carry the sprint. The original blink at tick 12 cancels
     * this motion and supplies the departure/arrival particles. Never adds
     * damage, changes attack reach or teleports through collision geometry.
     */
    public static void cinematicOpening(ServerPlayer player, ItemStack staff,
                                        long now, Vec3 targetPosition) {
        if (!(staff.getItem() instanceof OracleWeaponItem) || !eligible(player, false)) return;
        Vec3 direction = targetPosition.subtract(player.position()).multiply(1, 0, 1);
        if (direction.lengthSqr() < EPSILON) return;
        Motion motion = new Motion(player, staff, now + 6, 5, direction.normalize(),
                .80, 0, true, 0, false);
        replaceMotion(player, motion);
    }

    /** The ninth Furioso beat may make three short, collision-checked passes
     * through its target. Normal left-clicks NEVER enter this movement mode.
     * No extra damage is applied during any of the passes. */
    public static void scytheExit(ServerPlayer player, ItemStack staff,
                                  boolean cinematic, long now, Vec3 forward,
                                  boolean targetAvailable, double targetDistance) {
        boolean allowAir = cinematic && !supportedFloor(player);
        if (!eligible(player, allowAir)) return;
        Vec3 direction = forward.multiply(1, 0, 1);
        if (direction.lengthSqr() < EPSILON) return;
        if (!targetAvailable) {
            // Keep the original short finisher follow-through when no target
            // survived the ninth hit, rather than blind multi-block dashes.
            replaceMotion(player, new Motion(player, staff, now, 5,
                    direction.normalize(), cinematic ? .52 : .35,
                    0, true, 9, allowAir));
            return;
        }
        double reach = Math.min(3.2, Math.max(2.0, targetDistance * 2.0));
        Motion crossing = new Motion(player, staff, now, 24,
                direction.normalize(), reach, 0, true, 9, allowAir);
        crossing.specialScytheCrossing = true;
        replaceMotion(player, crossing);
    }

    private static void begin(ServerPlayer player, ItemStack staff, int form,
                              boolean finisher, boolean cinematic, long now,
                              Vec3 targetPosition) {
        // Only cinematic Furioso may dash after an air blink. Other movement
        // profiles retain the original supported-floor safety requirement.
        boolean allowAir = finisher && cinematic && !supportedFloor(player);
        if (!eligible(player, allowAir)) return;
        // XZ only: looking upward may never launch a grounded player into the air.
        Vec3 direction = targetPosition == null ? player.getLookAngle().multiply(1, 0, 1)
                : targetPosition.subtract(player.position()).multiply(1, 0, 1);
        if (direction.lengthSqr() < EPSILON)
            direction = player.getLookAngle().multiply(1, 0, 1);
        if (direction.lengthSqr() < EPSILON) return;
        direction = direction.normalize();
        // Each form has a distinct combat footprint. Side movement is relative to facing.
        // The lance is the only ordinary attack moving close to a full block.
        double[][] ordinary = {
                {}, {0, 0, 5}, {0, 0, 4}, {0, 0, 6},
                {0, 0, 5}, {0, 0, 6}, {0, 0, 7},
                // Lance (7): a long committed charge, not a nudge. Applies to
                // every ordinary thrust, hit or whiff, so the reach is paid for
                // by the gap it closes. 2.6 blocks over 8 ticks keeps the
                // smoothstep peak step under MAX_TICK_STEP for collision sweeps.
                {2.60, 0, 8}, {0, 0, 5}, {.65, 0, 10}
        };
        double[][] ultimate = {
                {}, {.50, -.22, 5}, {.72, 0, 4}, {.28, .45, 6},
                {.86, 0, 5}, {.37, 0, 5}, {.60, -.20, 6},
                {1.75, 0, 6}, {.10, -.52, 5}, {.48, 0, 5}
        };
        double[] profile = (finisher ? ultimate : ordinary)[Math.max(1, Math.min(9, form))];
        // CA has stronger follow-through, but never adds a full extra blink.
        double multiplier = cinematic ? 1.12 : 1.0;
        Motion motion = new Motion(player, staff, now, (int) profile[2], direction,
                profile[0] * multiplier, profile[1] * multiplier, finisher, form, allowAir);
        replaceMotion(player, motion);
    }

    private static void replaceMotion(ServerPlayer player, Motion motion) {
        Motion old = ACTIVE.remove(player.getUUID());
        if (old != null) restoreDisplay(old);
        ACTIVE.put(player.getUUID(), motion);
        if (motion.form == 7) OracleWeaponItem.setAttackDisplay(motion.staff, 17);
        if (DEBUG.contains(player.getUUID())) player.displayClientMessage(Component.literal(
                "§b[Rien motion] start form=" + motion.form + " forward="
                + String.format(java.util.Locale.ROOT, "%.2f", motion.forward)
                + " side=" + String.format(java.util.Locale.ROOT, "%.2f", motion.side)), false);
    }

    private static void restoreDisplay(Motion motion) {
        // A newer Furioso beat may already have replaced the display with another form.
        if (motion.form == 7) OracleWeaponItem.restoreAttackDisplay(motion.staff);
    }

    public static void cancel(ServerPlayer p) {
        Motion motion = ACTIVE.remove(p.getUUID());
        if (motion != null) restoreDisplay(motion);
    }

    public static void tick(MinecraftServer server) {
        long cutoff = server.overworld().getGameTime() - 100;
        ORDINARY_START.entrySet().removeIf(e -> e.getValue() < cutoff);
        // Vanilla never calls AttackEntity/AttackBlock for a swing that hits
        // nothing, so an air thrust has no server-side hook. The client intent
        // packet covers that, but it is only a hint: the observed swing flag on
        // the ServerPlayer is authoritative. It is set by the vanilla animate
        // packet for every swing, hit or miss, so the lance can never lose its
        // charge because a hint was dropped. ordinary() keeps its own cooldown
        // and attack-strength gate, so this can never chain extra dashes.
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            if (!p.swinging || OracleCombat.isFinisherActive(p.getUUID())) continue;
            ItemStack held = p.getMainHandItem();
            if (held.getItem() instanceof OracleWeaponItem
                    && OracleWeaponItem.getForm(held) == 7) {
                ordinary(p, held, p.serverLevel().getGameTime());
            }
        }
        Iterator<Map.Entry<UUID, Motion>> iterator = ACTIVE.entrySet().iterator();
        while (iterator.hasNext()) {
            Map.Entry<UUID, Motion> entry = iterator.next();
            Motion motion = entry.getValue();
            ServerPlayer player = server.getPlayerList().getPlayer(entry.getKey());
            if (player == null || !eligible(player, motion.allowAir) || player.serverLevel() != motion.level ||
                    player.getMainHandItem() != motion.staff ||
                    (motion.finisher && !OracleCombat.isFinisherActive(player.getUUID())) ||
                    (!motion.finisher && OracleCombat.isFinisherActive(player.getUUID()))) {
                restoreDisplay(motion);
                iterator.remove();
                continue;
            }
            int age = (int) (player.serverLevel().getGameTime() - motion.startTick);
            if (age <= 0) continue;
            if (age > motion.duration) {
                restoreDisplay(motion);
                iterator.remove();
                continue;
            }
            // Smooth acceleration, strong central thrust, controlled deceleration.
            double t = Math.min(1, (double) age / motion.duration);
            double progress = t * t * (3 - 2 * t);
            double delta = progress - motion.completed;
            motion.completed = progress;
            Vec3 right = new Vec3(-motion.facing.z, 0, motion.facing.x);
            // Skills only: after the ninth scythe blink we are on the FAR side
            // of the target. Travel backward through it, forward to the far side,
            // then backward once more. Each pass is eased; all are collision-safe.
            // Ordinary scythe swings use NONE of this displacement logic.
            double forwardProgress = progress;
            if (motion.specialScytheCrossing) {
                double pass = Math.min(2.999999, t * 3.0);
                int index = (int) pass;
                double phase = pass - index;
                double eased = phase * phase * (3 - 2 * phase);
                forwardProgress = index == 1 ? -1.0 + eased : -eased;
                if (age >= motion.duration) forwardProgress = -1.0;
            }
            double forwardDelta = forwardProgress - motion.forwardCompleted;
            motion.forwardCompleted = forwardProgress;
            Vec3 wanted = motion.facing.scale(motion.forward * forwardDelta)
                    .add(right.scale(motion.side * delta));
            double stepLimit = motion.specialScytheCrossing ? .72 : MAX_TICK_STEP;
            if (wanted.lengthSqr() > stepLimit * stepLimit)
                wanted = wanted.normalize().scale(stepLimit);
            if (!safelyMove(player, wanted, motion.allowAir,
                    motion.specialScytheCrossing)) {
                if (DEBUG.contains(player.getUUID())) player.displayClientMessage(
                    Component.literal("§c[Rien motion] BLOCKED after "
                        + String.format(java.util.Locale.ROOT, "%.2f", motion.actualDistance)
                        + " blocks (floor/collision)"), false);
                restoreDisplay(motion);
                iterator.remove(); // No delayed force when the animation is interrupted.
                continue;
            }
            motion.actualDistance += player.position().subtract(motion.lastPosition).horizontalDistance();
            motion.lastPosition = player.position();
            if (age >= motion.duration) {
                if (DEBUG.contains(player.getUUID())) player.displayClientMessage(
                    Component.literal("§a[Rien motion] completed "
                        + String.format(java.util.Locale.ROOT, "%.2f", motion.actualDistance)
                        + " blocks"), false);
                restoreDisplay(motion);
                iterator.remove();
            }
        }
    }

    private static boolean eligible(ServerPlayer player, boolean allowAir) {
        return player.isAlive() && !player.isSpectator() && !player.isPassenger()
                && !player.isFallFlying() && !player.isInWaterOrBubble()
                && !player.isInLava() && (allowAir || supportedFloor(player)) && !player.isSleeping();
    }

    /** Teleport/blink may clear the onGround bit for one tick although feet stand on
     * a solid block. Use actual collision support instead of that volatile flag. */
    private static boolean supportedFloor(ServerPlayer player) {
        return player.onGround() || supportedAt(player, player.getBoundingBox());
    }

    /** Probe the actual collision shape immediately below the feet. The old
     * full-block isFaceSturdy check rejected slabs, stairs and some landings,
     * prematurely turning three fast passes into little shuffling steps. */
    private static boolean supportedAt(ServerPlayer player, AABB hitbox) {
        double inset = 0.075;
        AABB probe = new AABB(hitbox.minX + inset, hitbox.minY - 0.11,
                hitbox.minZ + inset, hitbox.maxX - inset, hitbox.minY + 0.015,
                hitbox.maxZ - inset);
        return player.serverLevel().getBlockCollisions(player, probe).iterator().hasNext();
    }

    private static boolean safelyMove(ServerPlayer player, Vec3 wanted,
                                      boolean allowAir, boolean scytheCrossing) {
        if (wanted.lengthSqr() < EPSILON) return true;
        ServerLevel level = player.serverLevel();
        Vec3 start = player.position();
        // Sample the entire short sweep, not only the landing point.
        int samples = Math.max(2, (int) Math.ceil(wanted.length() / .12));
        for (int i = 1; i <= samples; i++) {
            Vec3 offset = wanted.scale((double) i / samples);
            Vec3 point = start.add(offset);
            BlockPos feet = BlockPos.containing(point);
            AABB shifted = player.getBoundingBox().move(offset);
            if (!level.getWorldBorder().isWithinBounds(feet)
                    || (scytheCrossing ? level.getBlockCollisions(player, shifted).iterator().hasNext()
                            : !level.noCollision(player, shifted))
                    || (!allowAir && !supportedAt(player, shifted))
                    || !level.getFluidState(feet).isEmpty()) return false;
        }
        player.move(MoverType.SELF, wanted);
        Vec3 traveled = player.position().subtract(start);
        if (traveled.horizontalDistanceSqr() < wanted.horizontalDistanceSqr() * .50) return false;
        // Explicit player-position synchronization: the client cannot accumulate
        // an out-of-sync, phantom dash velocity across a latency spike.
        player.teleportTo(player.getX(), player.getY(), player.getZ());
        player.fallDistance = 0;
        return true;
    }

    private static final class Motion {
        final ItemStack staff;
        final ServerLevel level;
        final long startTick;
        final int duration;
        final Vec3 facing;
        final double forward;
        final double side;
        final boolean finisher;
        final int form;
        final boolean allowAir;
        UUID scytheTargetId;
        Vec3 lastPosition;
        double actualDistance;
        double completed;
        double forwardCompleted;
        boolean specialScytheCrossing;

        Motion(ServerPlayer player, ItemStack staff, long tick, int duration, Vec3 facing,
               double forward, double side, boolean finisher, int form, boolean allowAir) {
            this.staff = staff;
            this.level = player.serverLevel();
            this.startTick = tick;
            this.duration = duration;
            this.facing = facing;
            this.forward = forward;
            this.side = side;
            this.finisher = finisher;
            this.form = form;
            this.allowAir = allowAir;
            this.lastPosition = player.position();
        }
    }
}
