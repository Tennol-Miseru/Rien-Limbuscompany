package io.github.oraclearsenal.client.mixin;

import io.github.oraclearsenal.client.LacrimosaCamera;
import net.minecraft.client.Camera;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.BlockGetter;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Camera.class)
public abstract class LacrimosaCameraMixin {
    // MC 1.21.1 intermediary runtime names. The old project had no usable refmap,
    // so use stable version-scoped intermediary targets, as FirstPersonWeaponMixin does.
    @Shadow(remap = false) protected abstract void method_19327(double x, double y, double z);
    @Shadow(remap = false) protected abstract void method_19325(float yaw, float pitch);
    @Shadow(remap = false) private boolean field_18719;

    @Inject(method = "method_19321", at = @At("TAIL"), remap = false)
    private void oraclearsenal$cinematic(BlockGetter level, Entity entity, boolean detached,
                                          boolean reverseView, float partialTicks, CallbackInfo ci) {
        LacrimosaCamera.Shot shot = LacrimosaCamera.sample(partialTicks);
        if (shot == null) return;
        this.field_18719 = true;
        method_19327(shot.position().x, shot.position().y, shot.position().z);
        method_19325(shot.yaw(), shot.pitch());
    }
}
