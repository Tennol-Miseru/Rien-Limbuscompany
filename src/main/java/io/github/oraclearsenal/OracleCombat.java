package io.github.oraclearsenal;

import com.mojang.brigadier.CommandDispatcher;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityAnchorArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.ChatFormatting;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.Iterator;
import java.util.List;
import java.util.UUID;

/** Server-authoritative combat and two deliberately distinct finishers. */
public final class OracleCombat {
    private static final List<Combo> COMBOS = new ArrayList<>();
    // Hits from ordinary left clicks resolve immediately on the server.
    // Separate hit throttling from air-swing packets (which only select animations).
    private static final java.util.Map<UUID, Long> ORDINARY_HITS = new java.util.HashMap<>();
    private static final java.util.Map<UUID, Long> SCYTHE_HITS = new java.util.HashMap<>();
    private static final long ORDINARY_HIT_INTERVAL = 8L;
    private static final int RANGE = 18;
    // Only nearby hostile creatures join an already-started Furioso. The
    // intentionally aimed first target remains eligible even if not hostile.
    private static final double FURIOSO_MULTI_TARGET_RANGE = 18.0;
    private static final double FURIOSO_MULTI_TARGET_HEIGHT = 9.0;
    private static final int FURIOSO_MAX_BLINK_CANDIDATES = 4;
    private static final long IDLE_REVERT_TICKS = 200L; // 10 seconds at 20 tps
    // First eight hits independently select from forms 1..8 (repeats are allowed,
    // but not consecutively); the ninth is ALWAYS form 9, the giant scythe.
    private static final int REPLICA_WINDUP = 8;
    private static final int REPLICA_STEP = 8;
    // Weapon impact resolves on the blink beat itself; no damage queue.
    // A single 20-tick scythe strike flows into a 12-tick still pose.
    // Both finishers play the same uninterrupted 32-tick animation.
    private static final int FINISHER_STAGES = 9;
    private static final int SCYTHE_MOTION_TICKS = 20;
    private static final int SCYTHE_HOLD_TICKS = 12;
    private static final int BLINK_PROTECTION_TICKS = 20; // one second at 20 TPS
    private static final int FINISHER_RESISTANCE_AMPLIFIER = 4; // Resistance V (during the cast)
    private static final int FINISHER_RECOVERY_AMPLIFIER = 3;  // Resistance IV (after completion)
    private static final int FINISHER_RECOVERY_TICKS = 100;   // 5 seconds at 20 TPS
    private static final float REPLICA_DAMAGE_MULTIPLIER = 1.4f;
    private static final float CRESCENDO_DAMAGE_MULTIPLIER = 1.4f;
    private static final float LACRIMOSA_DAMAGE_MULTIPLIER = 1.8f;
    private static final int REPLICA_RECOVERY = SCYTHE_MOTION_TICKS + SCYTHE_HOLD_TICKS - REPLICA_STEP;
    // Lacrimosa is a faster-starting, more forceful cinematic variation: its
    // per-weapon clips must match the SERVER-selected weapon, not a fixed movie.
    private static final int CA_BLINK_START = 12;
    private static final int CA_STEP = 8;
    // Stage 9 starts at tick 76. One sweep + 12-tick still pose
    // end the cinematic at tick 108, without an animation/model swap.
    private static final int CA_POSE_START = CA_BLINK_START
            + (FINISHER_STAGES - 1) * CA_STEP + SCYTHE_MOTION_TICKS;
    private static final int CA_DURATION = CA_POSE_START + SCYTHE_HOLD_TICKS;
    private static final long CRESCENDO_COOLDOWN_MS = 30_000L; // 30 real-time seconds, player-owned
    private static final int RANDOM_FORM_COUNT = 8;

    private OracleCombat() { }

    private enum Finisher { REPLICA, CRESCENDO }

    public static boolean isFinisherActive(UUID id) { return isComboActive(id); }

    public static void register() {
        // Player entities are reconstructed on death and End return. Carry the
        // persistent cooldown to the replacement before it is saved again.
        ServerPlayerEvents.COPY_FROM.register((oldPlayer, newPlayer, alive) -> {
            ((CrescendoCooldownAccess) newPlayer).oraclearsenal$setCrescendoReadyEpochMs(
                    ((CrescendoCooldownAccess) oldPlayer).oraclearsenal$getCrescendoReadyEpochMs());
            PrescriptTrialAccess before = (PrescriptTrialAccess) oldPlayer;
            PrescriptTrialAccess after = (PrescriptTrialAccess) newPlayer;
            after.oraclearsenal$setPrescriptCount(before.oraclearsenal$getPrescriptCount());
            after.oraclearsenal$setTrialPhase(before.oraclearsenal$getTrialPhase());
            after.oraclearsenal$setTrialPosition(before.oraclearsenal$getTrialX(),
                    before.oraclearsenal$getTrialY(), before.oraclearsenal$getTrialZ());
            after.oraclearsenal$setTrialBossId(before.oraclearsenal$getTrialBossId());
        });
        // Air swings do not fire AttackEntity/AttackBlock callbacks on the server.
        // Only an empty intent packet is sent: direction, weapon and cooldown
        // are all evaluated from the authoritative ServerPlayer.
        PayloadTypeRegistry.playC2S().register(CombatSwingPayload.TYPE, CombatSwingPayload.CODEC);
        ServerPlayNetworking.registerGlobalReceiver(CombatSwingPayload.TYPE,
                (payload, context) -> {
                    // Fabric play receivers already execute on the server thread.
                    ServerPlayer p = context.player();
                    CombatMovement.ordinary(p, p.getMainHandItem(), p.serverLevel().getGameTime());
                });
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) ->
                dispatcher.register(Commands.literal("rien")
                        .then(Commands.literal("motiondebug").executes(ctx -> {
                            ServerPlayer p = ctx.getSource().getPlayerOrException();
                            boolean enabled = CombatMovement.toggleDebug(p);
                            p.sendSystemMessage(Component.literal("Rien real-motion debug: " + (enabled ? "ON" : "OFF")));
                            return 1;
                        }))
                        .then(Commands.literal("crescendo").executes(ctx -> {
                            ServerPlayer p = ctx.getSource().getPlayerOrException();
                            ItemStack item = p.getMainHandItem();
                            if (!(item.getItem() instanceof OracleWeaponItem)) {
                                p.displayClientMessage(Component.translatable("message.oraclearsenal.need_weapon"), true);
                                return 0;
                            }
                            return startCrescendo(p, item) ? 1 : 0;
                        }))));

        ServerTickEvents.END_SERVER_TICK.register(server -> {
            // Low-HP black wisps are cosmetic, separate from Heart's gold effect.
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                RienDarkAura.lowHealthPlayer(player);
            }
            // Tick old motions before beginning the next Furioso beat. No teleport
            // step from the previous form can leak into the newly selected form.
            CombatMovement.tick(server);
            long cutoff = server.overworld().getGameTime() - 100L;
            ORDINARY_HITS.entrySet().removeIf(e -> e.getValue() < cutoff);
            SCYTHE_HITS.entrySet().removeIf(e -> e.getValue() < cutoff);
            Iterator<Combo> iterator = COMBOS.iterator();
            while (iterator.hasNext()) {
                Combo c = iterator.next();
                ServerPlayer p = server.getPlayerList().getPlayer(c.playerId);
                if (p == null || !p.isAlive() || p.getMainHandItem() != c.castStack
                        || p.serverLevel() != c.level) {
                    if (p != null) CombatMovement.cancel(p);
                    stopFinisher(c, p, p == null ? c.level.getGameTime() : p.serverLevel().getGameTime(), false);
                    iterator.remove();
                    continue;
                }
                long now = p.serverLevel().getGameTime();
                long age = now - c.startTick;
                int duration = c.mode == Finisher.REPLICA
                        ? REPLICA_WINDUP + FINISHER_STAGES * REPLICA_STEP + REPLICA_RECOVERY
                        : CA_DURATION;
                if (age >= duration) {
                    CombatMovement.cancel(p);
                    stopFinisher(c, p, now, true);
                    iterator.remove();
                    continue;
                }
                // Keep Resistance V active for every windup, blink, strike and
                // final still frame. Refresh only when close to expiration.
                refreshFinisherResistance(p, c);
                if (c.mode == Finisher.REPLICA) {
                    // Blink / morph / contact are three sequential actions, not one tick.
                    tickReplica(p, c, now);
                } else {
                    // V-key CA keeps the camera track, with per-weapon animation beats.
                    tickCrescendo(p, c, now);
                }
            }
            // Only the server mutates morph states; elapsed time continues in the inventory.
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                if (isComboActive(player.getUUID())) continue;
                long now = player.serverLevel().getGameTime();
                if (now % 20L == 0L) PrescriptTrial.tick(player);
                for (ItemStack stack : player.getInventory().items) {
                    revertIdleForm(player, stack, now);
                    if (now % 20L == 0L) OracleWeaponItem.refreshDisplayedName(stack);
                }
                for (ItemStack stack : player.getInventory().offhand) {
                    revertIdleForm(player, stack, now);
                    if (now % 20L == 0L) OracleWeaponItem.refreshDisplayedName(stack);
                }
            }
        });

        AttackBlockCallback.EVENT.register((player, world, hand, pos, direction) -> {
            if (player instanceof ServerPlayer p && hand == InteractionHand.MAIN_HAND) {
                ItemStack held = p.getMainHandItem();
                if (held.getItem() instanceof OracleWeaponItem && !isComboActive(p.getUUID())) {
                    CombatMovement.ordinary(p, held, p.serverLevel().getGameTime());
                }
            }
            return InteractionResult.PASS;
        });

        AttackEntityCallback.EVENT.register((player, world, hand, target, hit) -> {
            if (!(world instanceof ServerLevel) || hand != InteractionHand.MAIN_HAND)
                return InteractionResult.PASS;
            ItemStack stack = player.getMainHandItem();
            if (!(stack.getItem() instanceof OracleWeaponItem) || !(target instanceof LivingEntity living)
                    || !(player instanceof ServerPlayer p)) return InteractionResult.PASS;
            if (isComboActive(p.getUUID())) return InteractionResult.FAIL;
            if (living instanceof Player other && !p.canHarmPlayer(other)) return InteractionResult.FAIL;
            int form = OracleWeaponItem.getForm(stack);
            // Form 0 is a terminal, not a weapon. Vanilla unarmed damage only;
            // never invoke the nine-form damage table or earn Hermes charge.
            if (form == 0) return InteractionResult.PASS;
            if (player.getAttackStrengthScale(0.5f) < .65f) return InteractionResult.SUCCESS;
            long now = p.serverLevel().getGameTime();
            // Ordinary scythe no longer travels through targets. Animation and
            // optional lance motion are handled independently of hit resolution.
            CombatMovement.ordinary(p, stack, now);
            long previous = (form == 9 ? SCYTHE_HITS : ORDINARY_HITS)
                    .getOrDefault(p.getUUID(), Long.MIN_VALUE / 2);
            // All ordinary forms, including the scythe, have the same hit
            // interval. Keep the independent form-nine map for clean switches.
            // Heart must also shorten the mod's own hit throttle, not only
            // the vanilla ATTACK_SPEED attribute (8 -> 7 ticks).
            long minInterval = p.hasEffect(HeartEffect.HEART) ? 7L : ORDINARY_HIT_INTERVAL;
            if (now >= previous && now - previous < minInterval)
                return InteractionResult.SUCCESS;
            (form == 9 ? SCYTHE_HITS : ORDINARY_HITS).put(p.getUUID(), now);
            // Immediate damage and weapon-specific on-hit physics. SUCCESS
            // consumes the vanilla attack so damage is never applied twice.
            boolean successful = applyStage(p, living, form, false);
            p.resetAttackStrengthTicker();
            if (successful) {
                int count = OracleWeaponItem.addReplicaProgress(stack);
                if (count == 9) p.serverLevel().playSound(null, p.blockPosition(),
                        RienSounds.METAL_CLASH, SoundSource.PLAYERS, .65f, 1f);
            }
            return InteractionResult.SUCCESS;
        });
    }

    /** Replica: eight variable weapon beats and one fixed giant scythe. */
    private static void tickReplica(ServerPlayer p, Combo c, long now) {
        if (now < c.nextHitTick || c.stage >= FINISHER_STAGES) return;
        beginFinisherBeat(p, c, now);
        LivingEntity target = resolveTarget(p, c.beatTargetId);
        boolean inReach = target != null && p.distanceToSqr(target) <= 5.5 * 5.5;
        if (c.replicaLandingSucceeded && inReach && p.hasLineOfSight(target)) {
            if (!applyStage(p, target, c.activeForm, true, REPLICA_DAMAGE_MULTIPLIER))
                applyWhiff(p, c.activeForm, c.mode);
        } else {
            applyWhiff(p, c.activeForm, c.mode);
        }
        if (c.stage == FINISHER_STAGES) scytheFinish(p, target, c.lastAnchor, false);
        c.replicaLandingSucceeded = false;
        c.nextHitTick = c.startTick + REPLICA_WINDUP + c.stage * REPLICA_STEP;
    }

    /** Lacrimosa: immediate damage on a safe blink, followed by a brief recovery. */
    private static void tickCrescendo(ServerPlayer p, Combo c, long now) {
        if (now < c.nextHitTick || c.stage >= FINISHER_STAGES) return;
        beginFinisherBeat(p, c, now);
        LivingEntity target = resolveTarget(p, c.beatTargetId);
        boolean inReach = target != null && p.distanceToSqr(target) <= 5.5 * 5.5;
        caBeat(p, target, c.activeForm);
        if (c.caLandingSucceeded && inReach && p.hasLineOfSight(target)) {
            if (!applyCrescendoStage(p, target, c.activeForm, c.lacrimosaEnhanced))
                applyWhiff(p, c.activeForm, c.mode);
        } else {
            applyWhiff(p, c.activeForm, c.mode);
        }
        if (c.stage == FINISHER_STAGES) scytheFinish(p, target, c.lastAnchor, true);
        c.caLandingSucceeded = false;
        c.nextHitTick = c.startTick + CA_BLINK_START + c.stage * CA_STEP;
    }

    /** Centralized selection and teleport logic: stage != form after randomization. */
    private static void beginFinisherBeat(ServerPlayer p, Combo c, long now) {
        c.stage++;
        int form = c.stage == FINISHER_STAGES ? 9 : randomAttackForm(p, c.activeForm);
        c.activeForm = form;
        // Choose the enemy for THIS beat, not for the entire nine-hit art.
        // Try alternatives when a randomly chosen mob has no safe blink
        // position, so a single obstructed target does not waste a whole beat.
        List<LivingEntity> choices = nearbyFinisherTargets(p, c);
        CombatMovement.cancel(p);
        LivingEntity target = null;
        boolean landed = false;
        for (int index = 0; index < Math.min(choices.size(), FURIOSO_MAX_BLINK_CANDIDATES); index++) {
            LivingEntity candidate = choices.get(index);
            boolean airChase = c.mode == Finisher.CRESCENDO && isTargetAirborne(candidate);
            if (crescendoBlink(p, candidate, c.stage, c.angleSeed, form, airChase)) {
                target = candidate;
                landed = true;
                break;
            }
        }
        if (target == null && !choices.isEmpty()) {
            // Retain the attempted target for the whiff/finisher visuals only;
            // an unsafe landing can NEVER deal damage.
            target = choices.get(0);
        }
        if (target == null && c.lastAnchor != null) {
            // When everything died, continue the choreography at the last
            // known location, without inventing a living target to hit.
            landed = crescendoBlinkAt(p, c.lastAnchor, .6f,
                    c.lastAnchor.add(0, 1.2, 0), c.stage, c.angleSeed, form, false);
        }
        c.beatTargetId = target == null ? null : target.getUUID();
        if (target != null) {
            c.lastSelectedTargetId = target.getUUID();
            c.lastAnchor = target.position();
        }
        if (c.mode == Finisher.REPLICA) c.replicaLandingSucceeded = landed;
        else c.caLandingSucceeded = landed;

        ItemStack staff = p.getMainHandItem();
        OracleWeaponItem.setFinisherBeat(staff, form, c.stage, now);
        OracleWeaponItem.recordUse(staff, now);
        if (landed) CombatMovement.special(p, staff, form,
                c.mode == Finisher.CRESCENDO, now, target != null ? target.position() : c.lastAnchor);
        RienSounds.playChange(p.serverLevel(), p.blockPosition(), SoundSource.PLAYERS);
        spectralBeat(p.serverLevel(), p.position(), form);
    }

    private static int randomAttackForm(ServerPlayer p, int previous) {
        int form = p.getRandom().nextInt(RANDOM_FORM_COUNT) + 1;
        // No accidental immediately repeated morph. Other repeats are intentional,
        // so a given performance need not include every weapon form.
        while (form == previous) form = p.getRandom().nextInt(RANDOM_FORM_COUNT) + 1;
        return form;
    }

    /** Ordinary blink: random among the nine base weapons. */
    public static boolean blinkAndMorph(Player player, ItemStack stack) {
        if (!(player instanceof ServerPlayer p) || isComboActive(player.getUUID())) return false;
        LivingEntity target = acquireTarget(p);
        if (target == null) {
            p.displayClientMessage(Component.translatable("message.oraclearsenal.no_target"), true);
            return false;
        }
        CombatMovement.cancel(p);
        Vec3 before = p.position();
        Vec3 destination = findSafeBlink(p, target, p.getRandom().nextDouble() * 2 * Math.PI);
        if (destination == null) {
            p.displayClientMessage(Component.translatable("message.oraclearsenal.no_space"), true);
            return false;
        }
        ServerLevel level = p.serverLevel();
        RienAfterimages.departure(level, p, before);
        RienParticles.departure(level, before);
        teleportFacing(p, target, destination);
        RienParticles.arrival(level, destination);
        int form = p.getRandom().nextInt(9) + 1;
        OracleWeaponItem.setForm(stack, form);
        OracleWeaponItem.recordUse(stack, level.getGameTime());
        RienSounds.playChange(level, p.blockPosition(), SoundSource.PLAYERS);
        OracleWeaponItem.setAnimation(stack, 1, level.getGameTime());
        // Charge tiers 0/3/6/9 -> Resistance I/II/III/IV for 20 ticks.
        // Only a confirmed safe blink receives protection, not a failed cast.
        grantBlinkResistance(p, OracleWeaponItem.getReplicaProgress(stack));
        p.getCooldowns().addCooldown(stack.getItem(), 16);
        // The item title and teleport notice share a single translated name.
        // Show only the plain white short form name, never a numbered title.
        // Action-bar prescript is intentionally distinct from the short,
        // white inventory item title (e.g. "长枪").
        p.displayClientMessage(Component.translatable("message.oraclearsenal.weapon_prescript." + form)
                .withStyle(ChatFormatting.BLACK), true);
        return true;
    }

    /** Furioso [Crescendo]: nine successful hits charge the compact nine-blink art. */
    public static boolean startReplica(Player player, ItemStack stack) {
        if (!(player instanceof ServerPlayer p) || isComboActive(player.getUUID())) return false;
        int charge = OracleWeaponItem.getReplicaProgress(stack);
        if (charge < 9) {
            // The left-hotbar Hermes HUD already displays the current charge.
            return false;
        }
        LivingEntity target = acquireTarget(p);
        if (target == null) {
            p.displayClientMessage(Component.translatable("message.oraclearsenal.no_target"), true);
            return false;
        }
        if (!OracleWeaponItem.consumeReplica(stack)) return false;
        ServerLevel level = p.serverLevel();
        long now = level.getGameTime();
        CombatMovement.cancel(p);
        OracleWeaponItem.setForm(stack, 0);
        OracleWeaponItem.setAnimation(stack, 2, now);
        OracleWeaponItem.recordUse(stack, now);
        RienParticles.flourish(level, p.position());
        OracleWeaponItem.clearFinisherBeat(stack);
        Combo crescendo = new Combo(p.getUUID(), target.getUUID(), level, stack, Finisher.REPLICA, now,
                now + REPLICA_WINDUP, 0);
        crescendo.lastAnchor = target.position();
        crescendo.angleSeed = p.getRandom().nextDouble() * Math.PI * 2;
        COMBOS.add(crescendo);
        beginFinisherResistance(p, crescendo);
        HeartEffect.grant(p);
        p.displayClientMessage(Component.literal("Furioso-Replica")
                .withStyle(ChatFormatting.RED), true);
        return true;
    }

    /** V-key Furioso [Lacrimosa-Crescendo]: stronger nine-hit cinematic art. */
    public static boolean startCrescendo(ServerPlayer p, ItemStack stack) {
        if (isComboActive(p.getUUID())) {
            p.displayClientMessage(Component.translatable("message.oraclearsenal.busy"), true);
            return false;
        }
        ServerLevel level = p.serverLevel();
        long now = level.getGameTime();
        CrescendoCooldownAccess cooldown = (CrescendoCooldownAccess) p;
        // One-time migration of old V0.10.25 stack-bound cooldowns. Scan all
        // carried staves, so swapping slots cannot bypass a pre-upgrade timer.
        migrateLegacyCrescendoCooldown(p, cooldown, now);
        long currentMs = System.currentTimeMillis();
        long remainingMs = cooldown.oraclearsenal$getCrescendoReadyEpochMs() - currentMs;
        if (remainingMs > 0L) {
            p.displayClientMessage(Component.translatable("message.oraclearsenal.crescendo_cooldown",
                    (remainingMs + 999L) / 1000L), true);
            return false;
        }
        if (OracleWeaponItem.getReplicaProgress(stack) < 9) {
            p.displayClientMessage(Component.translatable("message.oraclearsenal.need_hermes_charge"), true);
            return false;
        }
        LivingEntity target = acquireTarget(p);
        if (target == null) {
            p.displayClientMessage(Component.translatable("message.oraclearsenal.no_target"), true);
            return false;
        }
        // Set a safe opening pose and lock the server-side target BEFORE starting the camera.
        Vec3 safe = findSafeBlink(p, target, p.getRandom().nextDouble() * Math.PI * 2);
        if (safe == null) {
            p.displayClientMessage(Component.translatable("message.oraclearsenal.no_space"), true);
            return false;
        }
        // Consume exactly one full nine-layer Hermes charge only after target
        // and safe launch space have both been confirmed. The 30s cooldown is
        // player-persistent, not stored in or reset by an ItemStack.
        if (!OracleWeaponItem.consumeReplica(stack)) return false;
        cooldown.oraclearsenal$setCrescendoReadyEpochMs(System.currentTimeMillis() + CRESCENDO_COOLDOWN_MS);
        CombatMovement.cancel(p);
        OracleWeaponItem.setForm(stack, 0);
        OracleWeaponItem.setAnimation(stack, 4, now);
        OracleWeaponItem.recordUse(stack, now);
        RienParticles.flourish(level, p.position());
        OracleWeaponItem.clearFinisherBeat(stack);
        Combo crescendo = new Combo(p.getUUID(), target.getUUID(), level, stack,
                Finisher.CRESCENDO, now, now + CA_BLINK_START, 0);
        // Snapshot HP before any scripted healing, damage or Resistance effects.
        crescendo.lacrimosaEnhanced = p.getHealth() < p.getMaxHealth() * 0.5f;
        crescendo.lastAnchor = target.position();
        crescendo.angleSeed = p.getRandom().nextDouble() * Math.PI * 2;
        COMBOS.add(crescendo);
        beginFinisherResistance(p, crescendo);
        HeartEffect.grant(p);
        // Twelve-tick opening: crouch/cover face, then a short real sprint.
        // The existing first blink remains at +12 and cancels this run-up.
        CombatMovement.cinematicOpening(p, stack, now, target.position());
        p.displayClientMessage(Component.literal(crescendo.lacrimosaEnhanced
                        ? "Furioso [Lacrimosa-Crescendo]" : "Furioso[Crescendo]")
                .withStyle(ChatFormatting.RED), true);
        return true;
    }

    /** Preserve active stack-local V0.10.25 timers when upgrading a saved world. */
    private static void migrateLegacyCrescendoCooldown(ServerPlayer player,
                                                        CrescendoCooldownAccess cooldown, long now) {
        long maximumLegacyTicks = 0L;
        for (ItemStack carried : player.getInventory().items) {
            if (carried.getItem() instanceof OracleWeaponItem) {
                maximumLegacyTicks = Math.max(maximumLegacyTicks,
                        OracleWeaponItem.getCrescendoReadyTick(carried) - now);
            }
        }
        for (ItemStack carried : player.getInventory().offhand) {
            if (carried.getItem() instanceof OracleWeaponItem) {
                maximumLegacyTicks = Math.max(maximumLegacyTicks,
                        OracleWeaponItem.getCrescendoReadyTick(carried) - now);
            }
        }
        if (maximumLegacyTicks > 0) {
            // Old item fields are never authoritative again after migration.
            long migrated = System.currentTimeMillis() + Math.min(600L, maximumLegacyTicks) * 50L;
            cooldown.oraclearsenal$setCrescendoReadyEpochMs(Math.max(
                    cooldown.oraclearsenal$getCrescendoReadyEpochMs(), migrated));
            for (ItemStack carried : player.getInventory().items) {
                if (carried.getItem() instanceof OracleWeaponItem) {
                    OracleWeaponItem.setCrescendoReadyTick(carried, 0L);
                }
            }
            for (ItemStack carried : player.getInventory().offhand) {
                if (carried.getItem() instanceof OracleWeaponItem) {
                    OracleWeaponItem.setCrescendoReadyTick(carried, 0L);
                }
            }
        }
    }

    private static void revertIdleForm(ServerPlayer player, ItemStack stack, long now) {
        if (!(stack.getItem() instanceof OracleWeaponItem) || OracleWeaponItem.getForm(stack) == 0) return;
        long last = OracleWeaponItem.getLastUseTick(stack);
        // Legacy stacks (without a timestamp) get their full ten seconds on first check.
        if (last < 0 || now < last) {
            OracleWeaponItem.recordUse(stack, now);
            return;
        }
        if (now - last < IDLE_REVERT_TICKS) return;
        OracleWeaponItem.setForm(stack, 0);
        // Clear timestamp to avoid retaining obsolete clock values between morphs.
        // The stored Replica charge and any other custom data survive.
        if (player.getMainHandItem() == stack || player.getOffhandItem() == stack) {
            RienSounds.playChange(player.serverLevel(), player.blockPosition(), SoundSource.PLAYERS);
        }
    }

    /** Resistance V is owned by this combo only while it is active. */
    private static void beginFinisherResistance(ServerPlayer p, Combo c) {
        MobEffectInstance before = p.getEffect(MobEffects.DAMAGE_RESISTANCE);
        if (before != null) {
            c.originalResistance = new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE,
                    before.getDuration(), before.getAmplifier(),
                    before.isAmbient(), before.isVisible(), before.showIcon());
        }
        // Do not hide an externally granted Resistance effect that is stronger
        // than V. If it expires mid-combo, refreshFinisherResistance takes over.
        if (before != null && before.getAmplifier() > FINISHER_RESISTANCE_AMPLIFIER) return;
        c.ownsResistance = before == null || before.getAmplifier() < FINISHER_RESISTANCE_AMPLIFIER
                || before.getDuration() < 10;
        if (c.ownsResistance) {
            p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 10,
                    FINISHER_RESISTANCE_AMPLIFIER, true, false, true));
        }
    }

    private static void refreshFinisherResistance(ServerPlayer p, Combo c) {
        MobEffectInstance current = p.getEffect(MobEffects.DAMAGE_RESISTANCE);
        if (current != null && current.getAmplifier() > FINISHER_RESISTANCE_AMPLIFIER) return;
        if (current != null && current.getAmplifier() == FINISHER_RESISTANCE_AMPLIFIER
                && current.getDuration() >= 5) return;
        c.ownsResistance = true;
        p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 10,
                FINISHER_RESISTANCE_AMPLIFIER, true, false, true));
    }

    private static void grantBlinkResistance(ServerPlayer p, int hermes) {
        int amplifier = Math.min(3, Math.max(0, hermes / 3));
        MobEffectInstance current = p.getEffect(MobEffects.DAMAGE_RESISTANCE);
        // Never downgrade a stronger external Resistance effect.
        if (current != null && current.getAmplifier() > amplifier) return;
        p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE,
                BLINK_PROTECTION_TICKS, amplifier, false, false, true));
    }

    /** Five-second Resistance IV after a full Furioso, never downgrade a
     * stronger effect or shorten an existing Resistance IV. */
    private static void grantFinisherRecoveryResistance(ServerPlayer p) {
        MobEffectInstance current = p.getEffect(MobEffects.DAMAGE_RESISTANCE);
        if (current != null && (current.getAmplifier() > FINISHER_RECOVERY_AMPLIFIER
                || (current.getAmplifier() == FINISHER_RECOVERY_AMPLIFIER
                    && current.getDuration() >= FINISHER_RECOVERY_TICKS))) return;
        p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE,
                FINISHER_RECOVERY_TICKS, FINISHER_RECOVERY_AMPLIFIER,
                false, false, true));
    }

    private static void stopFinisher(Combo c, ServerPlayer p, long now, boolean completed) {
        // Cancel our own Resistance V immediately on finish or interruption.
        // Restore the remaining part of a pre-cast effect before applying
        // post-finish protection, so we do not erase a stronger outside buff.
        if (p != null && c.ownsResistance) {
            MobEffectInstance active = p.getEffect(MobEffects.DAMAGE_RESISTANCE);
            if (active != null && active.getAmplifier() == FINISHER_RESISTANCE_AMPLIFIER) {
                p.removeEffect(MobEffects.DAMAGE_RESISTANCE);
                if (c.originalResistance != null) {
                    int elapsed = (int) Math.min(Integer.MAX_VALUE,
                            Math.max(0L, now - c.startTick));
                    int remaining = c.originalResistance.isInfiniteDuration()
                            ? c.originalResistance.getDuration()
                            : c.originalResistance.getDuration() - elapsed;
                    if (remaining > 0 || c.originalResistance.isInfiniteDuration()) {
                        MobEffectInstance prior = c.originalResistance;
                        p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE,
                                remaining, prior.getAmplifier(), prior.isAmbient(),
                                prior.isVisible(), prior.showIcon()));
                    }
                }
            }
        }
        // A COMPLETE nine-stage Furioso earns five seconds of Resistance IV.
        // Cancelling, changing items, disconnecting or dying does not earn it.
        if (completed && p != null && p.isAlive()) {
            grantFinisherRecoveryResistance(p);
        }
        OracleWeaponItem.setForm(c.castStack, 0);
        OracleWeaponItem.clearFinisherBeat(c.castStack);
        OracleWeaponItem.setAnimation(c.castStack, 0, now);
    }

    private static boolean isComboActive(UUID id) {
        return COMBOS.stream().anyMatch(c -> c.playerId.equals(id));
    }

    private static LivingEntity resolveTarget(ServerPlayer p, UUID targetId) {
        if (targetId == null) return null;
        Entity e = p.serverLevel().getEntity(targetId);
        if (e instanceof LivingEntity living && living.isAlive() && living.distanceToSqr(p) < 32 * 32) return living;
        return null;
    }

    /**
     * Build a fresh, server-authoritative target list for each Furioso strike.
     * The explicitly aimed initial victim remains eligible; any ADDITIONAL
     * targets must be real hostile mobs (Enemy), visible and nearby. This
     * deliberately excludes players, villagers, pets, and friendly NPCs.
     * No selected mob is permanently reserved: all nine hits may fan out.
     */
    private static List<LivingEntity> nearbyFinisherTargets(ServerPlayer p, Combo c) {
        List<LivingEntity> result = new ArrayList<>();
        LivingEntity original = resolveTarget(p, c.targetId);
        double maxDistanceSq = FURIOSO_MULTI_TARGET_RANGE * FURIOSO_MULTI_TARGET_RANGE;
        if (original != null && original.distanceToSqr(p) <= maxDistanceSq) {
            result.add(original);
        }
        AABB area = p.getBoundingBox().inflate(
                FURIOSO_MULTI_TARGET_RANGE, FURIOSO_MULTI_TARGET_HEIGHT,
                FURIOSO_MULTI_TARGET_RANGE);
        List<LivingEntity> hostiles = p.serverLevel().getEntitiesOfClass(LivingEntity.class, area,
                e -> e instanceof Enemy && e.isAlive() && e != p
                        && !p.isAlliedTo(e) && e.distanceToSqr(p) <= maxDistanceSq
                        && p.hasLineOfSight(e));
        for (LivingEntity hostile : hostiles) {
            if (original == null || !hostile.getUUID().equals(original.getUUID())) {
                result.add(hostile);
            }
        }
        // Preserve the old locked-target behavior when no other creature is
        // nearby; do not drop the combo simply because a target was launched.
        if (result.isEmpty() && original != null) result.add(original);
        // Fisher-Yates shuffle using the player's server RNG, no client choice.
        for (int i = result.size() - 1; i > 0; i--) {
            int j = p.getRandom().nextInt(i + 1);
            LivingEntity temp = result.get(i);
            result.set(i, result.get(j));
            result.set(j, temp);
        }
        // Distinguishable target switching when alternatives exist, without
        // forcing a switch if the previous target is the only safe one.
        if (result.size() > 1 && c.lastSelectedTargetId != null
                && result.get(0).getUUID().equals(c.lastSelectedTargetId)) {
            for (int i = 1; i < result.size(); i++) {
                if (!result.get(i).getUUID().equals(c.lastSelectedTargetId)) {
                    LivingEntity temp = result.get(0);
                    result.set(0, result.get(i));
                    result.set(i, temp);
                    break;
                }
            }
        }
        return result;
    }

    private static LivingEntity acquireTarget(ServerPlayer player) {
        Vec3 start = player.getEyePosition();
        Vec3 look = player.getLookAngle();
        AABB bounds = player.getBoundingBox().inflate(RANGE, RANGE / 2.0, RANGE);
        return player.serverLevel().getEntitiesOfClass(LivingEntity.class, bounds,
                        e -> e != player && e.isAlive() && !(e instanceof ArmorStand)
                                && player.hasLineOfSight(e)
                                && !(e instanceof Player other && !player.canHarmPlayer(other)))
                .stream().filter(e -> {
                    Vec3 to = e.getBoundingBox().getCenter().subtract(start);
                    double dist = to.length();
                    if (dist < .01 || dist > RANGE) return false;
                    double dot = to.normalize().dot(look);
                    return dot > (dist < 4 ? .65 : .91);
                })
                .min(Comparator.comparingDouble(e -> {
                    Vec3 to = e.getBoundingBox().getCenter().subtract(start);
                    double projected = to.dot(look);
                    double perpSq = Math.max(0, to.lengthSqr() - projected * projected);
                    return perpSq * 3 + projected * .06;
                })).orElse(null);
    }

    private static Vec3 findSafeBlink(ServerPlayer p, LivingEntity target, double startAngle) {
        double distance = target.getBbWidth() * .5 + p.getBbWidth() * .5 + .55;
        for (int height : new int[] {0, 1, -1, 2, -2}) {
            for (int i = 0; i < 12; i++) {
                double angle = startAngle + Math.PI * 2 * i / 12;
                Vec3 pos = new Vec3(target.getX() + Math.cos(angle) * distance,
                        target.getY() + height, target.getZ() + Math.sin(angle) * distance);
                BlockPos feet = BlockPos.containing(pos);
                if (!p.serverLevel().getWorldBorder().isWithinBounds(feet)) continue;
                BlockPos floor = feet.below();
                if (!p.serverLevel().getBlockState(floor).isFaceSturdy(p.serverLevel(), floor, Direction.UP)) continue;
                AABB moved = p.getBoundingBox().move(pos.subtract(p.position()));
                if (p.serverLevel().noCollision(p, moved)) return pos;
            }
        }
        return null;
    }

    private static void teleportFacing(ServerPlayer p, LivingEntity target, Vec3 destination) {
        p.teleportTo(destination.x, destination.y, destination.z);
        p.lookAt(EntityAnchorArgument.Anchor.EYES, target.getEyePosition());
        p.fallDistance = 0;
    }

    /** A launched foe must be pursued at their current height, not on the ground below. */
    private static boolean isTargetAirborne(LivingEntity target) {
        if (target.onGround() || target.isPassenger() || target.isInWaterOrBubble()
                || target.isInLava()) return false;
        return true;
    }

    /** Each strike in BOTH finishers requires a real, collision-safe displacement. */
    private static boolean crescendoBlink(ServerPlayer p, LivingEntity target, int stage,
                                          double seed, int form, boolean airChase) {
        return crescendoBlinkAt(p, target.position(), target.getBbWidth(),
                target.getEyePosition(), stage, seed, form, airChase);
    }

    /** Follow-through after target death uses the last known position, no corpse damage. */
    private static boolean crescendoBlinkAt(ServerPlayer p, Vec3 center, float targetWidth,
                                             Vec3 lookAt, int stage, double seed, int form,
                                             boolean airChase) {
        ServerLevel level = p.serverLevel();
        Vec3 before = p.position();
        // Lance: a longer run-up, rapier/awl: a compact lunge, heavy blades:
        // enough space to plant the forward foot. Blink still has a safe landing.
        double extraRunup = switch (form) {
            case 7 -> 1.55; case 4 -> .55; case 2 -> .45;
            case 6 -> .40; case 5 -> .35; default -> 0.0;
        };
        double baseRadius = (targetWidth + p.getBbWidth()) * .5 + .65 + extraRunup;
        // Golden-angle layout visits a different flank even for repeated weapons.
        double baseAngle = seed + stage * 2.399963229728653;
        Vec3 destination = null;
        if (airChase) {
            // Only V-key Lacrimosa takes this branch. Match the airborne
            // target's actual altitude; search several flanks for unobstructed
            // player-sized space. Teleporting is the existing Furioso ability;
            // no flight or block-phasing is added to ordinary attacks.
            outerAir:
            for (double elevation : new double[]{0, .4, -.4, .8, -.8}) {
                for (double extraRadius : new double[]{0, .55, 1.1}) {
                    for (int i = 0; i < 16; i++) {
                        double angle = baseAngle + Math.PI * 2 * i / 16;
                        double radius = baseRadius + extraRadius;
                        Vec3 pos = new Vec3(center.x + Math.cos(angle) * radius,
                                center.y + elevation, center.z + Math.sin(angle) * radius);
                        if (isSafeAirBlink(p, pos, before)) {
                            destination = pos;
                            break outerAir;
                        }
                    }
                }
            }
        }
        // A blocked aerial pursuit must never silently warp back to the ground.
        if (airChase && destination == null) return false;
        for (double extraRadius : new double[]{0.0, .55, 1.1}) {
            if (destination != null) break;
            for (int height : new int[]{0, 1, -1, 2, -2}) {
                if (destination != null) break;
                for (int i = 0; i < 16; i++) {
                    double offset = i == 0 ? 0 : ((i + 1) / 2) * Math.PI / 8
                            * ((i & 1) == 1 ? 1 : -1);
                    double angle = baseAngle + offset;
                    double radius = baseRadius + extraRadius;
                    Vec3 pos = new Vec3(center.x + Math.cos(angle) * radius,
                            center.y + height, center.z + Math.sin(angle) * radius);
                    // Never mistake reusing the current location for a teleport.
                    if (pos.distanceToSqr(before) < .8 * .8) continue;
                    BlockPos feet = BlockPos.containing(pos);
                    BlockPos floor = feet.below();
                    if (!level.getWorldBorder().isWithinBounds(feet)
                            || !level.getBlockState(floor).isFaceSturdy(level, floor, Direction.UP)
                            || !level.getFluidState(feet).isEmpty()
                            || !level.getFluidState(feet.above()).isEmpty()) continue;
                    AABB moved = p.getBoundingBox().move(pos.subtract(before));
                    if (!level.noCollision(p, moved)) continue;
                    destination = pos;
                    break;
                }
            }
        }
        if (destination == null) return false;
        RienAfterimages.departure(level, p, before, form,
                OracleWeaponItem.getAnimationMode(p.getMainHandItem()) == 4 ? 2 : 1);
        RienParticles.departure(level, before);
        p.teleportTo(destination.x, destination.y, destination.z);
        p.lookAt(EntityAnchorArgument.Anchor.EYES, lookAt);
        p.fallDistance = 0;
        RienParticles.arrival(level, destination);
        return true;
    }

    /** Final air-space collision test; never relies on a floor for V aerial pursuit. */
    private static boolean isSafeAirBlink(ServerPlayer player, Vec3 pos, Vec3 before) {
        ServerLevel level = player.serverLevel();
        BlockPos feet = BlockPos.containing(pos);
        BlockPos head = BlockPos.containing(pos.x, pos.y + player.getBbHeight(), pos.z);
        if (pos.distanceToSqr(before) < .8 * .8
                || pos.y < level.getMinBuildHeight()
                || pos.y + player.getBbHeight() >= level.getMaxBuildHeight()
                || !level.getWorldBorder().isWithinBounds(feet)
                || !level.getWorldBorder().isWithinBounds(head)
                || !level.getFluidState(feet).isEmpty()
                || !level.getFluidState(head).isEmpty()) return false;
        AABB destinationBox = player.getBoundingBox().move(pos.subtract(before));
        return level.noCollision(player, destinationBox);
    }

    private static void caBeat(ServerPlayer p, LivingEntity target, int stage) {
        ServerLevel level = p.serverLevel();
        Vec3 at = target != null ? target.position() : p.position().add(p.getLookAngle().scale(2));
        level.sendParticles(ParticleTypes.CRIT, at.x, at.y + .9, at.z,
                14 + stage * 2, .34, .48, .34, .13);
        // Hits are sounded exactly once by applyStage / applyWhiff.
        // Never layer vanilla sweep/trident noises on morph-driven strikes.
    }


    /** One shared on-hit effect system for ordinary, Replica and cinematic moves. */
    private static boolean applyCrescendoStage(ServerPlayer source, LivingEntity target,
                                               int form, boolean enhanced) {
        // Apply the selected cast's damage bonus on top of the existing
        // cinematic per-weapon base scale, including the ninth scythe strike.
        float castMultiplier = enhanced ? LACRIMOSA_DAMAGE_MULTIPLIER
                : CRESCENDO_DAMAGE_MULTIPLIER;
        float scale = (form == 9 ? 2.4f : 1.35f) * castMultiplier;
        boolean hit = applyStage(source, target, form, true, scale);
        if (!hit) return false;
        // Preserve the distinctive three-point cinematic lance puncture from
        // V0.10.26. Auxiliary punctures do not reapply on-hit statuses.
        if (form == 7) {
            ServerLevel level = source.serverLevel();
            for (int i = 0; i < 2; i++) {
                if (!target.isAlive()) break;
                target.invulnerableTime = 0;
                target.hurt(level.damageSources().playerAttack(source),
                        2.2f * castMultiplier);
                Vec3 puncture = target.position().add(0, target.getBbHeight() * .55, 0);
                level.sendParticles(ParticleTypes.CRIT, puncture.x, puncture.y, puncture.z,
                        12, .12, .12, .12, .05);
                RienSounds.playAttack(level, BlockPos.containing(puncture), SoundSource.PLAYERS, 7, .48f);
            }
        }
        return true;
    }

    /**
     * Scythe execution: pass THROUGH the target to the opposite flank, then
     * slide into a finishing pose. The exit is verified for floor/collision/fluid;
     * never teleport into a wall. No extra damage is dealt by the movement.
     */
    private static void scytheFinish(ServerPlayer p, LivingEntity target,
                                     Vec3 lastAnchor, boolean lacrimosa) {
        ServerLevel level = p.serverLevel();
        Vec3 impact = target != null ? target.position()
                : lastAnchor != null ? lastAnchor : p.position().add(p.getLookAngle().scale(2));
        Vec3 movement = impact.subtract(p.position()).multiply(1, 0, 1);
        if (movement.lengthSqr() < 0.01) movement = p.getLookAngle().multiply(1, 0, 1);
        if (movement.lengthSqr() < 0.01) movement = new Vec3(0, 0, 1);
        Vec3 through = movement.normalize();
        double radius = (target == null ? .65 : target.getBbWidth() * .5) + 1.45;
        Vec3 destination = null;
        boolean airFinish = lacrimosa && (target != null && isTargetAirborne(target)
                || !p.onGround());
        for (double side : new double[] {0, .55, -.55, 1.0, -1.0}) {
            Vec3 sideVector = new Vec3(-through.z, 0, through.x).scale(side);
            for (int height : new int[] {0, 1, -1, 2}) {
                Vec3 candidate = impact.add(through.scale(radius)).add(sideVector).add(0, height, 0);
                BlockPos feet = BlockPos.containing(candidate);
                BlockPos below = feet.below();
                if (airFinish) {
                    if (!isSafeAirBlink(p, candidate, p.position())) continue;
                } else if (!level.getWorldBorder().isWithinBounds(feet)
                        || !level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)
                        || !level.getFluidState(feet).isEmpty()
                        || !level.getFluidState(feet.above()).isEmpty()
                        || !level.noCollision(p, p.getBoundingBox().move(candidate.subtract(p.position())))) continue;
                destination = candidate;
                break;
            }
            if (destination != null) break;
        }
        if (destination != null) {
            RienAfterimages.departure(level, p, p.position(), 9,
                    lacrimosa ? 2 : 1);
            RienParticles.departure(level, p.position());
            p.teleportTo(destination.x, destination.y, destination.z);
            RienParticles.arrival(level, p.position());
            p.lookAt(EntityAnchorArgument.Anchor.EYES,
                    destination.add(through.scale(5)).add(0, 1.25, 0));
            p.fallDistance = 0;
            // End the finisher on the blink destination itself. The hit is
            // resolved once; avoid any extra back-and-forth travel after impact,
            // because that lingering motion can read as a twitch rather than a
            // deliberate attack. The final scythe animation now finishes in place.
        }
        level.sendParticles(ParticleTypes.SWEEP_ATTACK,
                impact.x, impact.y + 1.0, impact.z, lacrimosa ? 24 : 15, .75, .48, .75, .04);
        level.sendParticles(ParticleTypes.END_ROD,
                impact.x, impact.y + 1.0, impact.z, lacrimosa ? 48 : 24, .65, .55, .65, .07);
        level.playSound(null, BlockPos.containing(impact), RienSounds.SCYTHE_FINAL,
                SoundSource.PLAYERS, lacrimosa ? 1.0f : .78f, 1f);
    }

    private static void spectralBeat(ServerLevel level, Vec3 at, int form) {
        // Petals already appear at departure and landing during each real blink.
        // Do not layer the old soul / portal effect onto the weapon morph.
        if (form == 9) level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 1.1, at.z,
                45, .7, .9, .7, .13);
    }

    /** Shared hit resolver for player and NPC; only successful hits earn Hermes progress. */
    public static boolean applyStage(LivingEntity source, LivingEntity target, int form, boolean combo) {
        return applyStage(source, target, form, combo, 1f);
    }

    /** Cast-specific damage multipliers; ordinary attacks and NPCs are unchanged. */
    private static boolean applyStage(LivingEntity source, LivingEntity target, int form,
                                      boolean combo, float damageScale) {
        if (!(source.level() instanceof ServerLevel level) || !target.isAlive()) return false;
        if (source instanceof ServerPlayer && form == 0) return false;
        // Base per-form damage is shared with NPCs. Player Furioso multipliers
        // are applied by the respective cast; ordinary attack buffs remain separate.
        float damage = switch (form) {
            case 1 -> 3.8f; case 2 -> 2.8f; case 3 -> 4.6f; case 4 -> 3.3f;
            case 5 -> 5.3f; case 6 -> 6.8f; case 7 -> 4.2f; case 8 -> 3.1f;
            // The scythe is Rien's signature weapon, so its weapon damage is
            // the highest of the nine rather than the old 4.5 default.
            case 9 -> 10.0f;
            case 10 -> 4.0f; default -> 4.5f;
        };
        // V0.10.49: ordinary attacks use the weapon damage table for the nine
        // canonical forms. Rien shares it too, so the same weapon hits equally
        // hard in his hands and in the player's. Preserve their relative roles:
        // fast piercers/whip below heavy weapons. Extra form 10 and the combo
        // (Furioso / Rien's nine beats) keep the lower base table.
        if (!combo) {
            damage = switch (form) {
                case 1 -> 5.5f;  // hand axe       (+44.7%)
                case 2 -> 4.2f;  // thorn rapier   (+50.0%)
                case 3 -> 6.5f;  // great sword    (+41.3%)
                case 4 -> 5.0f;  // cross rapier   (+51.5%)
                case 5 -> 7.5f;  // sledgehammer   (+41.5%)
                case 6 -> 9.5f;  // colossal sword (+39.7%)
                case 7 -> 6.0f;  // lance          (+42.9%)
                case 8 -> 4.8f;  // long whip      (+54.8%)
                case 9 -> 10.0f; // giant scythe   (weapon damage 10)
                default -> damage;
            };
        }
        // NPC-only balance: Rien hits harder with the same weapon than the
        // player does, and enters a stronger second phase once the mask is off.
        if (source instanceof RienNpcEntity rien) {
            damage *= rien.hasRemovedMask() ? 2.2f : 1.75f;
        }
        damage *= damageScale;
        // The vanilla Attack Damage attribute modifier handles regular weapon
        // melee, but this mod resolves nine-form damage through target.hurt()
        // directly, bypassing that attribute. Apply Heart's +20% here for every
        // strike, ordinary and Furioso alike, so the buff stacks with the combo
        // multipliers instead of only covering normal swings.
        if (source.hasEffect(HeartEffect.HEART)) {
            damage *= HeartEffect.MELEE_DAMAGE_MULTIPLIER;
        }
        if (combo) target.invulnerableTime = 0;
        boolean hit = target.hurt(source instanceof Player player ? level.damageSources().playerAttack(player)
                : level.damageSources().mobAttack(source), damage);
        if (!hit) {
            if (target.isBlocking()) {
                level.playSound(null, target.blockPosition(), RienSounds.PARRY,
                        source instanceof Player ? SoundSource.PLAYERS : SoundSource.HOSTILE, .85f, 1f);
            }
            return false;
        }
        if (source instanceof ServerPlayer) {
            // Hit effects are applied once, after a confirmed damaging contact.
            // NPC combat keeps its original V0.10.26 passive mechanics unchanged.
            WeaponHitEffects.apply(source, target, form, combo,
                    damageScale > 1.05f);
        } else {
            applyPassive(source, target, form);
        }
        level.sendParticles(form == 9 ? ParticleTypes.END_ROD : ParticleTypes.SWEEP_ATTACK,
                target.getX(), target.getY() + target.getBbHeight() * .6, target.getZ(),
                form == 9 ? 26 : 8, .35, .35, .35, .04);
        level.sendParticles(ParticleTypes.CRIT, target.getX(), target.getY() + target.getBbHeight() * .5,
                target.getZ(), 12, .45, .4, .45, .18);
        SoundSource sourceChannel = source instanceof Player ? SoundSource.PLAYERS : SoundSource.HOSTILE;
        RienSounds.playAttack(level, target.blockPosition(), sourceChannel, form, combo ? .62f : .78f);
        // The supplied clang is used for steel-on-armor contacts, not every slash.
        if (target.getArmorValue() >= 8 && level.random.nextInt(3) == 0) {
            level.playSound(null, target.blockPosition(), RienSounds.METAL_CLASH,
                    sourceChannel, .38f, 1f);
        }
        if (source instanceof RienNpcEntity && level.random.nextInt(7) == 0) {
            level.playSound(null, source.blockPosition(), RienSounds.RIEN_EFFORT,
                    SoundSource.HOSTILE, .55f, 1f);
        }
        source.swing(InteractionHand.MAIN_HAND, true);
        if (combo && form == 9) {
            target.push(0, .55, 0);
            level.sendParticles(ParticleTypes.END_ROD, target.getX(), target.getY() + 1,
                    target.getZ(), 100, 1.2, .8, 1.2, .18);
        }
        return true;
    }

    private static void applyWhiff(ServerPlayer p, int form, Finisher mode) {
        Vec3 point = p.getEyePosition().add(p.getLookAngle().scale(2.5));
        p.serverLevel().sendParticles(form == 9 ? ParticleTypes.END_ROD : ParticleTypes.CRIT,
                point.x, point.y, point.z, 14, .55, .5, .55, .08);
        RienSounds.playAttack(p.serverLevel(), p.blockPosition(), SoundSource.PLAYERS, form, .40f);
        p.swing(InteractionHand.MAIN_HAND, true);
    }

    private static void applyPassive(LivingEntity source, LivingEntity target, int form) {
        switch (form) {
            case 1 -> target.knockback(.35, source.getX() - target.getX(), source.getZ() - target.getZ());
            case 2 -> target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 50, 0));
            case 3 -> target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 40, 0));
            case 4 -> target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 22, 0));
            case 5 -> target.knockback(1.1, source.getX() - target.getX(), source.getZ() - target.getZ());
            case 6 -> {
                target.knockback(.5, source.getX() - target.getX(), source.getZ() - target.getZ());
                target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 35, 1));
            }
            case 7 -> target.knockback(.5, source.getX() - target.getX(), source.getZ() - target.getZ());
            case 8 -> { // The long whip staggers briefly rather than chaining down a victim.
                target.knockback(.30, source.getX() - target.getX(), source.getZ() - target.getZ());
                target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 18, 0));
            }
            case 9 -> target.addEffect(new MobEffectInstance(MobEffects.WITHER, 55, 0));
            default -> { }
        }
    }

    private static final class Combo {
        private final UUID playerId;
        private final UUID targetId;
        private UUID beatTargetId;
        private UUID lastSelectedTargetId;
        private final ServerLevel level;
        private final ItemStack castStack;
        private final Finisher mode;
        private final long startTick;
        private long nextHitTick;
        private int stage;
        private int activeForm;
        private double angleSeed;
        private Vec3 lastAnchor;
        private boolean replicaLandingSucceeded;
        private boolean caLandingSucceeded;
        private boolean lacrimosaEnhanced;
        private boolean ownsResistance;
        private MobEffectInstance originalResistance;

        private Combo(UUID playerId, UUID targetId, ServerLevel level, ItemStack castStack,
                      Finisher mode, long startTick, long nextHitTick, int stage) {
            this.playerId = playerId;
            this.targetId = targetId;
            this.level = level;
            this.castStack = castStack;
            this.mode = mode;
            this.startTick = startTick;
            this.nextHitTick = nextHitTick;
            this.stage = stage;
        }
    }
}
