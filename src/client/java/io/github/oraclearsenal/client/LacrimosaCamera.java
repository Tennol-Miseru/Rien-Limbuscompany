package io.github.oraclearsenal.client;

import io.github.oraclearsenal.OracleWeaponItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Weapon-led cinematic shot list for the V-key finisher.
 * There is no automatic orbit. Each server-selected weapon cuts to its own
 * stable composition; only a gentle dolly follows that weapon's attack.
 * These offsets never rotate/move the player or affect hit detection.
 */
public final class LacrimosaCamera {
    public record Shot(Vec3 position, float yaw, float pitch) { }

    /** Offsets in the actor's frame: horizontal camera-right, camera-forward, height.
     *  The dolly changes translation, never yaw/orbit, during an eight-tick beat. */
    private record Framing(double right, double forward, double height,
                           double focusHeight, double dollyRight, double dollyForward) { }

    // Front-quarter opening: clearly shows the hand-to-face crouch and run-up.
    // No orbit; the first blink at tick 12 cuts to the selected weapon shot.
    private static final Framing INTRO = new Framing(2.55, 3.35, 1.52, 1.18, -.35, -.45);
    // Final pose: front-quarter view shows the chest/torso twist instead of
    // photographing the back of the player as the old negative forward offset did.
    private static final Framing FINAL = new Framing(2.45, 3.65, 1.65, 1.28, 0, 0);
    private static final Framing[] WEAPON_SHOTS = {
            INTRO,
            new Framing(-2.05, 2.85, 1.72, 1.20, .36, -.20), // 1 hand axe: 3/4 front chop
            new Framing(1.85, 3.35, 1.48, 1.10, -.25, -.40), // 2 awl: side-on thrust
            new Framing(-3.85, 1.20, 1.70, 1.10, .42, -.22), // 3 greatsword: broad side view
            new Framing(3.00, 2.10, 1.65, 1.18, -.45, .15), // 4 rapier: profile of the lunge
            new Framing(-2.25, 3.65, 1.18, 1.27, .15, -.20), // 5 hammer: low-angle impact
            new Framing(3.85, 2.15, 1.36, 1.18, -.22, -.17), // 6 colossal: wide low side
            new Framing(4.15, 0.75, 1.55, 1.10, -.75, -.10), // 7 lance: side-tracking charge
            new Framing(-3.15, 1.70, 2.60, 1.16, .35, -.35), // 8 whip: space for wide arc
            new Framing(3.65, 2.00, 2.10, 1.18, -.40, -.10)  // 9 scythe: full-body crossing
    };

    private LacrimosaCamera() { }

    public static float age(float partialTicks) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null || !mc.player.isAlive()) return -1f;
        ItemStack stack = mc.player.getMainHandItem();
        if (!(stack.getItem() instanceof OracleWeaponItem)
                || OracleWeaponItem.getAnimationMode(stack) != 4) return -1f;
        float tick = (float) (mc.level.getGameTime() - OracleWeaponItem.getAnimationStart(stack)) + partialTicks;
        return tick >= 0 && tick < 108 ? tick : -1f;
    }

    public static boolean active() { return age(0) >= 0; }

    // No final-pose mouse lock: users may adjust facing/look throughout the
    // finale. Camera framing remains collision-safe and follows the actor.

    public static Shot sample(float partialTicks) {
        float elapsed = age(partialTicks);
        if (elapsed < 0) return null;
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.level == null) return null;
        ItemStack stack = p.getMainHandItem();
        int stage = OracleWeaponItem.getFinisherStage(stack);
        int form = OracleWeaponItem.getForm(stack);
        // The ninth beat starts on 76; one scythe sweep lasts 20 ticks.
        // Only frame the final side/back silhouette after its blade comes down.
        boolean outro = elapsed >= 96f;
        Framing shot = outro ? FINAL : stage <= 0 ? INTRO
                : WEAPON_SHOTS[Mth.clamp(form, 1, 9)];

        Vec3 actor = new Vec3(Mth.lerp(partialTicks, p.xo, p.getX()),
                Mth.lerp(partialTicks, p.yo, p.getY()),
                Mth.lerp(partialTicks, p.zo, p.getZ()));
        double radians = Math.toRadians(Mth.rotLerp(partialTicks, p.yRotO, p.getYRot()));
        // Vanilla look direction: yaw 0 points +Z. Side = actor-local right.
        Vec3 forward = new Vec3(-Math.sin(radians), 0, Math.cos(radians));
        Vec3 right = new Vec3(Math.cos(radians), 0, Math.sin(radians));

        double beatAge = stage > 0
                ? mc.level.getGameTime() - OracleWeaponItem.getFinisherBeatTick(stack) + partialTicks
                : elapsed;
        // Short, non-rotating dolly: a different frame per form, not an orbit.
        double t = Mth.clamp(beatAge / (stage > 0 ? 7d : 12d), 0d, 1d);
        double ease = t * t * (3d - 2d * t);
        double sideOffset = shot.right + (outro ? 0 : shot.dollyRight * ease);
        double forwardOffset = shot.forward + (outro ? 0 : shot.dollyForward * ease);

        Vec3 focus = actor.add(0, shot.focusHeight, 0);
        Vec3 desired = actor.add(right.scale(sideOffset)).add(forward.scale(forwardOffset))
                .add(0, shot.height, 0);
        // Cut shots must never force the camera inside a solid block.
        BlockHitResult obstacle = mc.level.clip(new ClipContext(focus, desired,
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
        if (obstacle.getType() == HitResult.Type.BLOCK) {
            Vec3 distance = desired.subtract(focus);
            if (distance.lengthSqr() > 1.0e-6) {
                desired = obstacle.getLocation().subtract(distance.normalize().scale(.18));
            }
        }
        Vec3 look = focus.subtract(desired);
        float yaw = (float) Math.toDegrees(Math.atan2(-look.x, look.z));
        float pitch = (float) -Math.toDegrees(Math.atan2(look.y,
                Math.sqrt(look.x * look.x + look.z * look.z)));
        return new Shot(desired, yaw, pitch);
    }
}
