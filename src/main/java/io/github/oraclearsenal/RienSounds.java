package io.github.oraclearsenal;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.Level;

/**
 * One server-authoritative sound routing table shared by player and Rien NPC.
 * sounds.json provides randomized variants, drawn only from the user's own archive.
 * Never play a vanilla teleport sound for teleport + weapon morph.
 */
public final class RienSounds {
    public static final SoundEvent WEAPON_CHANGE = registerSound("weapon_change");
    public static final SoundEvent SLASH = registerSound("strike_slash");
    public static final SoundEvent IMPACT = registerSound("strike_impact");
    public static final SoundEvent PIERCE = registerSound("strike_pierce");
    public static final SoundEvent WHIP = registerSound("strike_whip");
    public static final SoundEvent SCYTHE = registerSound("strike_scythe");
    public static final SoundEvent SCYTHE_FINAL = registerSound("strike_scythe_final");
    public static final SoundEvent METAL_CLASH = registerSound("metal_clash");
    public static final SoundEvent PARRY = registerSound("parry");
    public static final SoundEvent RIEN_EFFORT = registerSound("rien_effort");
    public static final SoundEvent RIEN_LAUGH = registerSound("rien_laugh");
    public static final SoundEvent MASK_DROP = registerSound("mask_drop");
    public static final SoundEvent MASK_SCARS = registerSound("mask_scars");
    public static final SoundEvent PRESCRIPT_BEEP = registerSound("prescript_beep");

    private RienSounds() { }

    private static SoundEvent registerSound(String name) {
        ResourceLocation id = OracleArsenal.id(name);
        return Registry.register(BuiltInRegistries.SOUND_EVENT, id, SoundEvent.createVariableRangeEvent(id));
    }

    public static void register() {
        OracleArsenal.LOGGER.info("Rien sound events registered: morph, slash, impact, pierce, whip, scythe, voice and mask.");
    }

    public static SoundEvent attackForForm(int form) {
        return switch (form) {
            case 2, 4, 7 -> PIERCE;
            case 5 -> IMPACT;
            case 8 -> WHIP;
            case 9 -> SCYTHE;
            default -> SLASH; // 1 hand axe, 3 greatsword, 6 colossal blade
        };
    }

    public static void playChange(Level level, BlockPos where, SoundSource source) {
        level.playSound(null, where, WEAPON_CHANGE, source, .82f, 1f);
    }

    public static void playAttack(Level level, BlockPos where, SoundSource source, int form, float volume) {
        level.playSound(null, where, attackForForm(form), source, volume, 1f);
    }
}
