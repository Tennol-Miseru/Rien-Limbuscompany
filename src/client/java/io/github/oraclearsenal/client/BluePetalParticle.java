package io.github.oraclearsenal.client;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;

/** Blue petals slowly settle and sway rather than behaving like portal smoke. */
public final class BluePetalParticle extends TextureSheetParticle {
    private final SpriteSet sprites;
    private final double driftPhase;
    private final float spin;

    private BluePetalParticle(ClientLevel level, double x, double y, double z,
                              double vx, double vy, double vz, SpriteSet sprites) {
        super(level, x, y, z);
        this.sprites = sprites;
        this.lifetime = 32 + this.random.nextInt(26);
        this.gravity = .035f;
        this.friction = .95f;
        this.hasPhysics = false;
        this.quadSize = (.085f + this.random.nextFloat() * .095f);
        this.xd = vx * .3 + (this.random.nextDouble() - .5) * .045;
        this.yd = -.018 - this.random.nextDouble() * .022;
        this.zd = vz * .3 + (this.random.nextDouble() - .5) * .045;
        this.driftPhase = this.random.nextDouble() * Math.PI * 2;
        this.spin = (this.random.nextFloat() - .5f) * .13f;
        this.roll = this.random.nextFloat() * (float) (Math.PI * 2);
        this.oRoll = this.roll;
        this.pickSprite(sprites);
    }

    @Override
    public void tick() {
        this.xd += Math.sin(this.driftPhase + this.age * .16) * .0016;
        this.zd += Math.cos(this.driftPhase + this.age * .13) * .0016;
        super.tick();
        this.oRoll = this.roll;
        this.roll += this.spin;
        this.setSpriteFromAge(this.sprites);
        // Gradual fade as the petals reach the ground.
        if (this.age > this.lifetime * .7f) {
            this.alpha = Math.max(0f, (this.lifetime - this.age) / (this.lifetime * .3f));
        }
    }

    @Override
    public ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_TRANSLUCENT;
    }

    public static final class Provider implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;

        public Provider(SpriteSet sprites) { this.sprites = sprites; }

        @Override
        public Particle createParticle(SimpleParticleType type, ClientLevel level,
                                        double x, double y, double z,
                                        double vx, double vy, double vz) {
            return new BluePetalParticle(level, x, y, z, vx, vy, vz, sprites);
        }
    }
}
