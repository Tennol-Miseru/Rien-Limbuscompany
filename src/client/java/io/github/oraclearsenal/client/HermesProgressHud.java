package io.github.oraclearsenal.client;

import io.github.oraclearsenal.OracleArsenal;
import io.github.oraclearsenal.OracleWeaponItem;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.DeltaTracker;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.Util;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.entity.HumanoidArm;

/**
 * Compact Replica charge status to the LEFT of the vanilla hotbar.
 * The ItemStack's replica_progress is authoritative; this is a purely client-side visual.
 */
public final class HermesProgressHud {
    private static final ResourceLocation ICON = OracleArsenal.id("textures/gui/hermes_progress_hud.png");
    private static final int ICON_TEXTURE_WIDTH = 28;
    private static final int ICON_TEXTURE_HEIGHT = 27;
    private static final int ICON_WIDTH = 28;
    private static final int ICON_HEIGHT = 27;
    private static final long PULSE_DURATION_MS = 420L;

    private static int lastVisibleProgress;
    private static long pulseStartMs = -1L;
    private static java.util.UUID lastPlayerId;

    private HermesProgressHud() { }

    public static void register() {
        HudRenderCallback.EVENT.register(HermesProgressHud::render);
    }

    private static void render(GuiGraphics graphics, DeltaTracker delta) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null || mc.options.hideGui || mc.player.isSpectator()) {
            reset();
            return;
        }
        if (!mc.player.getUUID().equals(lastPlayerId)) {
            lastPlayerId = mc.player.getUUID();
            lastVisibleProgress = 0;
            pulseStartMs = -1L;
        }

        // Prefer the wielded staff. If not wielded, preserve a stored charge
        // indicator from an inventory staff, so switching slots will not hide it.
        int progress = findProgress(mc);
        if (progress <= 0) {
            lastVisibleProgress = 0;
            pulseStartMs = -1L;
            return; // Zero stacks: no icon, no number, no placeholder.
        }

        long nowMs = Util.getMillis();
        if (progress > lastVisibleProgress) {
            pulseStartMs = nowMs; // Every increment, including 8 -> 9, restarts the pop animation.
        }
        lastVisibleProgress = progress;

        float t = pulseStartMs < 0 ? 1.0f : Mth.clamp((nowMs - pulseStartMs) / (float) PULSE_DURATION_MS, 0.0f, 1.0f);
        float punch = t >= 1.0f ? 0.0f : Mth.sin(t * (float) Math.PI);
        float scale = 1.0f + 0.22f * punch;
        float bounceY = -4.0f * punch;

        int barLeft = graphics.guiWidth() / 2 - 91;
        // Vanilla draws a 29-pixel offhand slot immediately to the left of
        // the hotbar for right-handed players. Calculate the entire HUD width
        // (icon + numeric charge), not just the 28px icon, to avoid overlap.
        int hudWidth = ICON_WIDTH + 1 + mc.font.width(Integer.toString(progress));
        boolean leftOffhand = !mc.player.getOffhandItem().isEmpty()
                && mc.player.getMainArm() == HumanoidArm.RIGHT;
        int safeRight = leftOffhand ? barLeft - 29 - 10 : barLeft - 7;
        int x = Math.max(3, safeRight - hudWidth);
        int y = graphics.guiHeight() - 31;
        // Small GUI widths may not leave room left of the offhand slot. In that
        // case render the charge ABOVE the slot rather than on top of it.
        if (leftOffhand && x + hudWidth > barLeft - 29 - 6) {
            x = Math.max(3, barLeft - hudWidth - 7);
            y = graphics.guiHeight() - 61;
        }

        graphics.pose().pushPose();
        graphics.pose().translate(x + ICON_WIDTH / 2.0f, y + ICON_HEIGHT / 2.0f + bounceY, 0);
        graphics.pose().scale(scale, scale, 1.0f);
        graphics.pose().translate(-ICON_WIDTH / 2.0f, -ICON_HEIGHT / 2.0f, 0);
        graphics.blit(ICON, 0, 0, 0.0f, 0.0f, ICON_WIDTH, ICON_HEIGHT,
                ICON_TEXTURE_WIDTH, ICON_TEXTURE_HEIGHT);
        graphics.pose().popPose();

        // Show only the current Hermes charge (1 through 9); zero is hidden above.
        // The number pulses alongside the icon on increment.
        String count = Integer.toString(progress);
        int textColor = progress == 9 ? 0xFFF9DE9D : (punch > 0.03f ? 0xFFAFF9FF : 0xFF57D8F7);
        graphics.drawString(mc.font, count, x + 29, y + 10 - Math.round(bounceY * 0.5f), textColor, true);
    }

    private static int findProgress(Minecraft mc) {
        ItemStack held = mc.player.getMainHandItem();
        if (held.getItem() instanceof OracleWeaponItem) return OracleWeaponItem.getReplicaProgress(held);
        ItemStack offhand = mc.player.getOffhandItem();
        if (offhand.getItem() instanceof OracleWeaponItem) return OracleWeaponItem.getReplicaProgress(offhand);
        int highest = 0;
        for (ItemStack item : mc.player.getInventory().items) {
            if (item.getItem() instanceof OracleWeaponItem) {
                highest = Math.max(highest, OracleWeaponItem.getReplicaProgress(item));
            }
        }
        return highest;
    }

    private static void reset() {
        lastPlayerId = null;
        lastVisibleProgress = 0;
        pulseStartMs = -1L;
    }
}
