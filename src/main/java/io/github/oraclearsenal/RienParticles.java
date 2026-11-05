package io.github.oraclearsenal;

import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

/** Falling-blue-petal effect; every teleport uses three to five petals in total. */
public final class RienParticles {
    public static final SimpleParticleType BLUE_PETAL = FabricParticleTypes.simple();

    private RienParticles() { }

    public static void register() {
        Registry.register(BuiltInRegistries.PARTICLE_TYPE, OracleArsenal.id("blue_petal"), BLUE_PETAL);
    }

    private static void spawn(ServerLevel level, Vec3 pos, int count) {
        level.sendParticles(BLUE_PETAL, pos.x, pos.y + 1.4, pos.z,
                count, .34, .48, .34, .025);
    }

    /** One or two petals at the position we leave. */
    public static void departure(ServerLevel level, Vec3 pos) {
        spawn(level, pos, 1 + level.random.nextInt(2));
    }

    /** Two or three petals at the position where we arrive.
     * Combined with departure(), one teleport produces three to five petals.
     */
    public static void arrival(ServerLevel level, Vec3 pos) {
        spawn(level, pos, 2 + level.random.nextInt(2));
    }

    /** A standalone skill activation / flourish uses three to five petals. */
    public static void flourish(ServerLevel level, Vec3 pos) {
        spawn(level, pos, 3 + level.random.nextInt(3));
    }
}
