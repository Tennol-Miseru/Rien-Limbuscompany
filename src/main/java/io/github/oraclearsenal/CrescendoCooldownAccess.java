package io.github.oraclearsenal;

/** Implemented by the Player NBT mixin. Cooldowns belong to the caster, not an item. */
public interface CrescendoCooldownAccess {
    long oraclearsenal$getCrescendoReadyEpochMs();
    void oraclearsenal$setCrescendoReadyEpochMs(long epochMs);
}
