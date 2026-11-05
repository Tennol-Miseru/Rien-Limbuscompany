package io.github.oraclearsenal.mixin;

import io.github.oraclearsenal.CrescendoCooldownAccess;
import io.github.oraclearsenal.PrescriptTrialAccess;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Persist the V skill's ready time with the player save, regardless of held staff. */
@Mixin(Player.class)
public abstract class PlayerCrescendoCooldownMixin implements CrescendoCooldownAccess, PrescriptTrialAccess {
    @Unique private static final String COOLDOWN_NBT = "oraclearsenal_crescendo_ready_epoch_ms";
    @Unique private long oraclearsenal$readyEpochMs;
    @Unique private int oraclearsenal$prescriptCount;
    @Unique private int oraclearsenal$trialPhase;
    @Unique private int oraclearsenal$trialX;
    @Unique private int oraclearsenal$trialY;
    @Unique private int oraclearsenal$trialZ;
    @Unique private UUID oraclearsenal$trialBossId;

    @Override public int oraclearsenal$getPrescriptCount() { return oraclearsenal$prescriptCount; }
    @Override public void oraclearsenal$setPrescriptCount(int count) {
        oraclearsenal$prescriptCount = Math.max(0, Math.min(9, count));
    }
    @Override public int oraclearsenal$getTrialPhase() { return oraclearsenal$trialPhase; }
    @Override public void oraclearsenal$setTrialPhase(int phase) {
        oraclearsenal$trialPhase = Math.max(0, Math.min(3, phase));
    }
    @Override public int oraclearsenal$getTrialX() { return oraclearsenal$trialX; }
    @Override public int oraclearsenal$getTrialY() { return oraclearsenal$trialY; }
    @Override public int oraclearsenal$getTrialZ() { return oraclearsenal$trialZ; }
    @Override public void oraclearsenal$setTrialPosition(int x, int y, int z) {
        oraclearsenal$trialX = x; oraclearsenal$trialY = y; oraclearsenal$trialZ = z;
    }
    @Override public UUID oraclearsenal$getTrialBossId() { return oraclearsenal$trialBossId; }
    @Override public void oraclearsenal$setTrialBossId(UUID id) { oraclearsenal$trialBossId = id; }


    @Override
    public long oraclearsenal$getCrescendoReadyEpochMs() { return oraclearsenal$readyEpochMs; }

    @Override
    public void oraclearsenal$setCrescendoReadyEpochMs(long epochMs) {
        oraclearsenal$readyEpochMs = Math.max(0L, epochMs);
    }

    // Minecraft 1.21.1 intermediary selectors. Explicitly remap=false to match
    // the existing project's refmap-free mixin setup.
    @Inject(method = "method_5652", at = @At("TAIL"), remap = false)
    private void oraclearsenal$saveCooldown(CompoundTag nbt, CallbackInfo ci) {
        if (oraclearsenal$readyEpochMs > 0L) nbt.putLong(COOLDOWN_NBT, oraclearsenal$readyEpochMs);
        nbt.putInt("oraclearsenal_prescript_count", oraclearsenal$prescriptCount);
        nbt.putInt("oraclearsenal_trial_phase", oraclearsenal$trialPhase);
        if (oraclearsenal$trialPhase > 0) {
            nbt.putInt("oraclearsenal_trial_x", oraclearsenal$trialX);
            nbt.putInt("oraclearsenal_trial_y", oraclearsenal$trialY);
            nbt.putInt("oraclearsenal_trial_z", oraclearsenal$trialZ);
        }
        if (oraclearsenal$trialBossId != null) nbt.putUUID("oraclearsenal_trial_boss", oraclearsenal$trialBossId);
    }

    @Inject(method = "method_5749", at = @At("TAIL"), remap = false)
    private void oraclearsenal$loadCooldown(CompoundTag nbt, CallbackInfo ci) {
        oraclearsenal$readyEpochMs = Math.max(0L, nbt.getLong(COOLDOWN_NBT));
        oraclearsenal$setPrescriptCount(nbt.getInt("oraclearsenal_prescript_count"));
        oraclearsenal$setTrialPhase(nbt.getInt("oraclearsenal_trial_phase"));
        oraclearsenal$trialX = nbt.getInt("oraclearsenal_trial_x");
        oraclearsenal$trialY = nbt.getInt("oraclearsenal_trial_y");
        oraclearsenal$trialZ = nbt.getInt("oraclearsenal_trial_z");
        oraclearsenal$trialBossId = nbt.hasUUID("oraclearsenal_trial_boss")
                ? nbt.getUUID("oraclearsenal_trial_boss") : null;
    }
}
