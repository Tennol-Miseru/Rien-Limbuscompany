package io.github.oraclearsenal;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;

import java.util.List;

/**
 * Rien's cracked porcelain half-mask. A vanilla helmet renders its transparent,
 * asymmetric armor texture on the player's head without a custom entity renderer.
 * The actual wearable mesh and head rotations are supplied by Minecraft 1.21.1.
 */
public final class RienMaskItem extends ArmorItem {
    public RienMaskItem(Holder<ArmorMaterial> material, Properties properties) {
        super(material, Type.HELMET, properties);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context,
                                List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.oraclearsenal.rien_mask")
                .withStyle(ChatFormatting.GOLD));
        tooltip.add(Component.translatable("tooltip.oraclearsenal.rien_mask_equipment")
                .withStyle(ChatFormatting.GRAY));
        super.appendHoverText(stack, context, tooltip, flag);
    }
}
