package io.github.oraclearsenal;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

/**
 * Weapon-specific impact effects for PLAYER combat. The NPC's existing passive
 * table is deliberately not changed. All physics, effects and particles are
 * server authoritative, and run only after target.hurt() succeeds.
 *
 * intensity: ordinary=0, nine-blink Replica=1, cinematic Lacrimosa=2.
 * The cinematic lance's extra punctures do not repeat this method.
 */
public final class WeaponHitEffects {
    private WeaponHitEffects() { }

    public static void apply(LivingEntity source, LivingEntity target, int form,
                             boolean combo, boolean cinematic) {
        if (!(source.level() instanceof ServerLevel level)) return;
        int intensity = cinematic ? 2 : combo ? 1 : 0;
        double x = target.getX();
        double y = target.getY() + target.getBbHeight() * 0.55;
        double z = target.getZ();
        switch (form) {
            case 1 -> { // Hand axe — stagger on a compact diagonally downward chop.
                target.knockback(.30 + intensity * .12,
                        source.getX() - x, source.getZ() - z);
                effect(target, MobEffects.WEAKNESS, 28 + intensity * 10, 0);
                level.sendParticles(ParticleTypes.CRIT, x, y + .1, z,
                        9 + intensity * 4, .24, .21, .24, .08);
            }
            case 2 -> { // Awl — upward launch on impact.
                launch(target, intensity);
                double baseY = target.getY() + .35;
                for (int i = 0; i < 4; i++) {
                    level.sendParticles(ParticleTypes.END_ROD,
                            x, baseY + i * .35, z, 4 + intensity,
                            .12, .09, .12, .025);
                }
            }
            case 3 -> { // Greatsword — broad sweep displaces the enemy sideways.
                Vec3 horizontal = target.position().subtract(source.position()).multiply(1, 0, 1);
                if (horizontal.lengthSqr() > .0001) {
                    Vec3 right = new Vec3(-horizontal.z, 0, horizontal.x).normalize();
                    Vec3 current = target.getDeltaMovement();
                    double lateral = .20 + intensity * .07;
                    target.setDeltaMovement(current.x + right.x * lateral,
                            current.y, current.z + right.z * lateral);
                    target.hurtMarked = true;
                }
                level.sendParticles(ParticleTypes.SWEEP_ATTACK, x, y, z,
                        12 + intensity * 5, .55, .22, .55, .035);
            }
            case 4 -> { // Rapier — precision puncture, short poison tick.
                effect(target, MobEffects.POISON, 28 + intensity * 10, 0);
                level.sendParticles(ParticleTypes.CRIT, x, y, z,
                        15 + intensity * 3, .12, .12, .12, .09);
            }
            case 5 -> { // Hammer — forceful knockback plus Slowness II on impact.
                target.knockback(1.0 + intensity * .23,
                        source.getX() - x, source.getZ() - z);
                Vec3 v = target.getDeltaMovement();
                target.setDeltaMovement(v.x, Math.max(v.y, .12), v.z);
                target.hurtMarked = true;
                effect(target, MobEffects.MOVEMENT_SLOWDOWN, 55 + intensity * 13, 1);
                level.sendParticles(ParticleTypes.POOF, x, target.getY() + .20, z,
                        12 + intensity * 7, .42, .16, .42, .045);
            }
            case 6 -> { // Colossal greatsword — heavy suppressing downward cleave.
                effect(target, MobEffects.WEAKNESS, 55 + intensity * 10, 0);
                if (!target.onGround() && !target.isInWaterOrBubble()) {
                    Vec3 v = target.getDeltaMovement();
                    target.setDeltaMovement(v.x * .7,
                            Math.min(v.y, -.16 - intensity * .10), v.z * .7);
                    target.hurtMarked = true;
                }
                level.sendParticles(ParticleTypes.CRIT, x, y + .3, z,
                        17 + intensity * 5, .39, .32, .39, .09);
            }
            case 7 -> { // Knight lance — pierce and shove in the charging direction.
                target.knockback(.58 + intensity * .15,
                        source.getX() - x, source.getZ() - z);
                level.sendParticles(ParticleTypes.CRIT, x, y, z,
                        17 + intensity * 6, .10, .12, .10, .09);
            }
            case 8 -> { // LONG WHIP — a lateral snap and short movement disruption.
                target.knockback(.27 + intensity * .10,
                        source.getX() - x, source.getZ() - z);
                effect(target, MobEffects.MOVEMENT_SLOWDOWN, 32 + intensity * 9, 1);
                level.sendParticles(ParticleTypes.SWEEP_ATTACK, x, y, z,
                        12 + intensity * 6, .70, .20, .70, .035);
            }
            case 9 -> { // Scythe — lingering Wither after a broad execution arc.
                effect(target, MobEffects.WITHER, 55 + intensity * 13, 0);
                level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, x, y, z,
                        14 + intensity * 6, .46, .42, .46, .025);
            }
            default -> { }
        }
    }

    private static void effect(LivingEntity target,
                               net.minecraft.core.Holder<net.minecraft.world.effect.MobEffect> type,
                               int ticks, int amplifier) {
        target.addEffect(new MobEffectInstance(type, ticks, amplifier));
    }

    private static void launch(LivingEntity target, int intensity) {
        if (target.isPassenger() || target.isInWaterOrBubble() || target.isInLava()) return;
        double lift = switch (intensity) {
            case 1 -> .66;
            case 2 -> .80;
            default -> .52;
        };
        // Large bosses and giant mobs should not be thrown several blocks high.
        if (target.getBbHeight() > 3.0 || target.getBbWidth() > 2.5)
            lift = Math.min(lift, .20);
        Vec3 movement = target.getDeltaMovement();
        target.setDeltaMovement(movement.x * .48, Math.max(movement.y, lift), movement.z * .48);
        target.hurtMarked = true;
        target.fallDistance = 0;
    }
}
