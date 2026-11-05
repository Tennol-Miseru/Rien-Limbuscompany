package io.github.oraclearsenal.client.mixin;

import io.github.oraclearsenal.client.LacrimosaCamera;
import net.minecraft.client.Camera;
import net.minecraft.client.renderer.GameRenderer;
import org.joml.Matrix4f;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Prevent first-person hand rendering over the third-person CA camera. */
@Mixin(GameRenderer.class)
public abstract class LacrimosaHandsMixin {
    @Inject(method = "method_3172", at = @At("HEAD"), cancellable = true, remap = false)
    private void oraclearsenal$hideHands(Camera camera, float partialTicks, Matrix4f projection, CallbackInfo ci) {
        if (LacrimosaCamera.active()) ci.cancel();
    }
}
