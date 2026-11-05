package io.github.oraclearsenal.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import io.github.oraclearsenal.OracleWeaponItem;
import io.github.oraclearsenal.PrescriptPagerItem;
import io.github.oraclearsenal.client.FirstPersonCombatMotion;
import io.github.oraclearsenal.client.OraclePlayerAnimations;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.ItemInHandRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import com.mojang.math.Axis;

/**
 * First-person held-item + arm animation. The item is always rendered through
 * vanilla's hand pipeline; this Mixin modifies the shared matrix so both arm
 * and weapon follow the same weapon-specific, smooth, authored motion.
 *
 * IMPORTANT: method_3228 is ItemInHandRenderer.renderArmWithItem for MC 1.21.1.
 * Keep remap=false for packaged intermediary clients (existing project rule).
 */
@Mixin(ItemInHandRenderer.class)
public abstract class FirstPersonWeaponMixin {
    @Unique private boolean oraclearsenal$posePushed;

    @Inject(method = "method_3228", at = @At("HEAD"), remap = false)
    private void oraclearsenal$before(AbstractClientPlayer player, float partialTicks, float pitch,
                                       InteractionHand hand, float swing, ItemStack stack, float equip,
                                       PoseStack pose, MultiBufferSource buffers, int light, CallbackInfo ci) {
        oraclearsenal$posePushed = false;
        if (hand != InteractionHand.MAIN_HAND
                || (!(stack.getItem() instanceof OracleWeaponItem)
                && !(stack.getItem() instanceof PrescriptPagerItem))) return;
        if (Minecraft.getInstance().level == null) return;

        pose.pushPose();
        oraclearsenal$posePushed = true;
        double clock = Minecraft.getInstance().level.getGameTime() + partialTicks;
        if (stack.getItem() instanceof PrescriptPagerItem) {
            double since = clock - PrescriptPagerItem.getReceiveTick(stack);
            float pulse = since >= 0 && since < 14
                    ? (float) Math.sin(Math.PI * since / 14.0) : 0f;
            pose.translate(0, .19f * pulse, -.16f * pulse);
            pose.mulPose(Axis.XP.rotationDegrees(-14 * pulse));
            pose.mulPose(Axis.ZP.rotationDegrees(6 * pulse));
            return;
        }

        boolean leftHand = player.getMainArm() == HumanoidArm.LEFT;
        int mode = OracleWeaponItem.getAnimationMode(stack);
        double elapsed = clock - OracleWeaponItem.getAnimationStart(stack);
        int form = OracleWeaponItem.getForm(stack);
        // No idle breathing during the final scythe hold: a truly fixed POSE.
        int stage = OracleWeaponItem.getFinisherStage(stack);
        double holdAge = clock - OracleWeaponItem.getFinisherBeatTick(stack);
        boolean finalHold = (mode == 2 || mode == 4) && stage == 9
                && holdAge >= 0 && holdAge < 32;
        if (!finalHold) pose.translate(0, Math.sin(clock * .095) * .006, 0);

        if (mode == 1 && elapsed >= 0 && elapsed < 12) {
            FirstPersonCombatMotion.draw(pose, elapsed / 12, leftHand);
            return;
        }

        if ((mode == 2 || mode == 4) && elapsed >= 0 && elapsed < (mode == 2 ? 104 : 108)) {
            double beatAge = clock - OracleWeaponItem.getFinisherBeatTick(stack);
            if (stage >= 1 && stage <= 9 && beatAge >= -1 && beatAge <= (stage == 9 ? 32 : 18)) {
                if (stage == 9) {
                    // Stage nine makes one decisive 20-tick finishing sweep.
                    FirstPersonCombatMotion.finalSequence(pose,
                            Math.min(1, Math.max(0, beatAge) / 20.0), leftHand);
                } else {
                    // Use SERVER-chosen weapon form and beat clock.
                    FirstPersonCombatMotion.strike(pose, form,
                            Math.max(0, beatAge) / 8.0, leftHand);
                }
            } else if (stage == 0) {
                if (mode == 4) {
                    FirstPersonCombatMotion.cinematicOpening(pose,
                            Math.min(1, elapsed / 12.0), leftHand);
                } else {
                    FirstPersonCombatMotion.windup(pose,
                            Math.min(1, elapsed / 8.0), leftHand);
                }
            } else if (stage == 9) {
                FirstPersonCombatMotion.finalSequence(pose, 1, leftHand);
            }
            return;
        }

        // Locally observed arm-swing starts immediately on client, even when
        // the player misses or hits a block. Server mode=3 catches confirmed
        // attacks; never double-play the same attack when the sync arrives.
        double localAge = OraclePlayerAnimations.getOrdinarySwingAge(player, clock);
        int ordinaryDuration = 12;
        double age = mode == 3 && elapsed >= 0 && elapsed < ordinaryDuration
                ? elapsed : localAge;
        if (mode != 2 && mode != 4 && age >= 0 && age < ordinaryDuration) {
            // Normal scythe is one swipe. Repeated crossing is skill-only.
            FirstPersonCombatMotion.strike(pose, form <= 0 ? 1 : form,
                    age / ordinaryDuration, leftHand);
        }
    }

    @Inject(method = "method_3228", at = @At("RETURN"), remap = false)
    private void oraclearsenal$after(AbstractClientPlayer player, float partialTicks, float pitch,
                                      InteractionHand hand, float swing, ItemStack stack, float equip,
                                      PoseStack pose, MultiBufferSource buffers, int light, CallbackInfo ci) {
        if (oraclearsenal$posePushed) {
            pose.popPose();
            oraclearsenal$posePushed = false;
        }
    }
}
