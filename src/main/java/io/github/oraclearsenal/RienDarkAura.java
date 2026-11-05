package io.github.oraclearsenal;

import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import org.joml.Vector3f;

/** Server-side cosmetic black aura. Both profiles use black smoke with dark
 * ash wisps; neither sets fire, adds a potion effect, or changes combat stats. */
public final class RienDarkAura {
    private static final DustParticleOptions ASH = new DustParticleOptions(
            new Vector3f(0.055f, 0.052f, 0.077f), 1.12f);
    private RienDarkAura() { }

    /** The NPC's dramatic three-second Furioso windup, intensifying as it nears release. */
    public static void npcWindup(ServerLevel level, LivingEntity entity, int ticksRemaining) {
        if (!entity.isAlive() || entity.isInvisible() || ticksRemaining < 0) return;
        // Send just three packets per four ticks; keep the effect bounded to
        // the actor, avoiding hundreds of particles per tick on a busy server.
        if ((entity.tickCount & 3) != 0) return;
        float intensity = 1.0f - Math.min(60, ticksRemaining) / 60.0f;
        int smokeCount = 3 + Math.round(intensity * 6);
        int ashCount = 3 + Math.round(intensity * 6);
        double r = .38 + intensity * .28;
        double y = entity.getY() + entity.getBbHeight() * .50;
        level.sendParticles(ParticleTypes.LARGE_SMOKE,
                entity.getX(), y, entity.getZ(), smokeCount,
                r, entity.getBbHeight() * .34, r, .012 + intensity * .018);
        level.sendParticles(ParticleTypes.SMOKE,
                entity.getX(), y + .10, entity.getZ(), smokeCount,
                r * 1.2, entity.getBbHeight() * .42, r * 1.2, .018);
        level.sendParticles(ASH,
                entity.getX(), y, entity.getZ(), ashCount,
                r * 1.1, entity.getBbHeight() * .35, r * 1.1, .010);
    }

    /** Below-half-health player: restrained wisps below the head and camera. */
    public static void lowHealthPlayer(ServerPlayer player) {
        if (!player.isAlive() || player.isSpectator() || player.isInvisible()
                || player.getHealth() >= player.getMaxHealth() * .5f
                || player.tickCount % 8 != 0) return;
        ServerLevel level = player.serverLevel();
        double height = Math.min(player.getBbHeight() * .45, .80);
        level.sendParticles(ParticleTypes.SMOKE,
                player.getX(), player.getY() + height, player.getZ(),
                1, .28, .20, .28, .005);
        if (player.tickCount % 16 == 0) {
            level.sendParticles(ASH,
                    player.getX(), player.getY() + height * .8, player.getZ(),
                    1, .30, .17, .30, .003);
        }
    }
}
