package io.github.oraclearsenal;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import org.joml.Vector3f;

/** "Heart": a one-minute post-Furioso buff shared by players and Rien NPC.
 * Vanilla attribute modifiers are removed automatically when the effect expires.
 * The subtle particles are spawned around the waist and lower torso, away from the camera.
 */
public final class HeartEffect extends MobEffect {
    public static final int DURATION_TICKS = 20 * 60;
    public static final float MELEE_DAMAGE_MULTIPLIER = 1.20f;
    public static final Holder<MobEffect> HEART = Registry.registerForHolder(
            BuiltInRegistries.MOB_EFFECT, OracleArsenal.id("heart"), new HeartEffect());

    private static final DustParticleOptions GOLD = new DustParticleOptions(
            new Vector3f(0.96f, 0.67f, 0.18f), 0.66f);
    private static final DustParticleOptions PALE_GOLD = new DustParticleOptions(
            new Vector3f(1.00f, 0.87f, 0.42f), 0.52f);

    private HeartEffect() {
        super(MobEffectCategory.BENEFICIAL, 0xE9B549);
        addAttributeModifier(Attributes.ATTACK_SPEED,
                OracleArsenal.id("heart_attack_speed"), .15,
                AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        addAttributeModifier(Attributes.MOVEMENT_SPEED,
                OracleArsenal.id("heart_movement_speed"), .15,
                AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        addAttributeModifier(Attributes.ATTACK_DAMAGE,
                OracleArsenal.id("heart_melee_damage"), .20,
                AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
    }

    /** Invoked only after an eligible Furioso activation was accepted. */
    public static void grant(LivingEntity entity) {
        if (!entity.isAlive() || entity.level().isClientSide) return;
        entity.addEffect(new MobEffectInstance(HEART, DURATION_TICKS, 0,
                false, false, true));
    }

    /** Three sparse, separated wisp positions per 4 ticks, averaging 13.33
     * particles/second: one gold, one pale gold, and one optional extra gold
     * (2/3 probability). Vanilla potion swirls remain suppressed. */
    @Override
    public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
        return duration % 4 == 0;
    }

    @Override
    public boolean applyEffectTick(LivingEntity entity, int amplifier) {
        if (entity.level() instanceof ServerLevel level && entity.isAlive() && !entity.isInvisible()) {
            double angle = level.random.nextDouble() * Math.PI * 2.0;
            double radius = .32 + level.random.nextDouble() * .20;
            double x = entity.getX() + Math.cos(angle) * radius;
            double z = entity.getZ() + Math.sin(angle) * radius;
            double y = entity.getY() + Math.min(entity.getBbHeight() * .64,
                    .22 + level.random.nextDouble() * .78);
            level.sendParticles(GOLD, x, y, z, 1, .012, .032, .012, .005);

            // Put highlights on a different side of the actor; two particles
            // at one coordinate appear as a single dot in third person.
            double highlightAngle = angle + 2.15;
            double highlightRadius = .34 + level.random.nextDouble() * .16;
            double highlightY = entity.getY() + Math.min(entity.getBbHeight() * .67,
                    .30 + level.random.nextDouble() * .70);
            level.sendParticles(PALE_GOLD,
                    entity.getX() + Math.cos(highlightAngle) * highlightRadius,
                    highlightY,
                    entity.getZ() + Math.sin(highlightAngle) * highlightRadius,
                    1, .008, .020, .008, .005);

            if (level.random.nextInt(3) != 0) {
                double extraAngle = angle + 4.25;
                double extraRadius = .30 + level.random.nextDouble() * .22;
                double extraY = entity.getY() + Math.min(entity.getBbHeight() * .62,
                        .18 + level.random.nextDouble() * .82);
                level.sendParticles(GOLD,
                        entity.getX() + Math.cos(extraAngle) * extraRadius,
                        extraY,
                        entity.getZ() + Math.sin(extraAngle) * extraRadius,
                        1, .010, .028, .010, .005);
            }
        }
        return true;
    }
}
