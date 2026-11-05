package io.github.oraclearsenal;

import net.fabricmc.fabric.api.item.v1.FabricItem;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.Level;

import java.util.List;

public final class OracleWeaponItem extends Item implements FabricItem {
    public OracleWeaponItem(Properties properties) {
        super(properties);
    }

    /**
     * Morphs and synchronized attack states change custom data many times during
     * Furioso. Do not lower and re-equip the SAME held staff after each update;
     * the first-person choreography handles the visual transition instead.
     * Actual slot/item changes still use vanilla's equip animation.
     */
    @Override
    public boolean allowComponentsUpdateAnimation(Player player, InteractionHand hand,
                                                    ItemStack oldStack, ItemStack newStack) {
        return false;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (hand != InteractionHand.MAIN_HAND) return InteractionResultHolder.pass(stack);
        if (player.getCooldowns().isOnCooldown(this)) return InteractionResultHolder.fail(stack);
        if (level.isClientSide) return InteractionResultHolder.success(stack);
        // Even a right-click with no target is an attempt to use the manifested weapon.
        if (getForm(stack) > 0) recordUse(stack, level.getGameTime());
        boolean ok = player.isShiftKeyDown()
                ? OracleCombat.startReplica(player, stack)
                : OracleCombat.blinkAndMorph(player, stack);
        return ok ? InteractionResultHolder.success(stack) : InteractionResultHolder.fail(stack);
    }

    /** Use the short translated weapon name as the displayed name of a manifested form.
     * The untransformed terminal keeps its original item name. No custom name is
     * persisted, so switching forms changes the title immediately and does not
     * interfere with anvil-renamed stacks. */
    @Override
    public Component getName(ItemStack stack) {
        int form = getForm(stack);
        return form > 0 && form <= 9
                ? Component.translatable("form.oraclearsenal." + form)
                    .withStyle(ChatFormatting.WHITE)
                : super.getName(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.oraclearsenal.blink").withStyle(ChatFormatting.AQUA));
        tooltip.add(Component.translatable("tooltip.oraclearsenal.ultimate").withStyle(ChatFormatting.LIGHT_PURPLE));
        tooltip.add(Component.literal("代行·赫尔墨斯 " + getReplicaProgress(stack) + "/9 层")
                .withStyle(ChatFormatting.BLACK));
        tooltip.add(Component.translatable("tooltip.oraclearsenal.crescendo").withStyle(ChatFormatting.DARK_PURPLE));
        super.appendHoverText(stack, context, tooltip, flag);
    }

    /** Nine successful ordinary weapon hits prime one Furioso-Replica use (max one stored). */
    public static int getReplicaProgress(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null) return 0;
        return Math.max(0, Math.min(9, data.copyTag().getInt("replica_progress")));
    }

    public static int addReplicaProgress(ItemStack stack) {
        int count = Math.min(9, getReplicaProgress(stack) + 1);
        setInt(stack, "replica_progress", count);
        return count;
    }

    public static boolean consumeReplica(ItemStack stack) {
        if (getReplicaProgress(stack) < 9) return false;
        setInt(stack, "replica_progress", 0);
        return true;
    }

    public static long getCrescendoReadyTick(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? 0L : data.copyTag().getLong("crescendo_ready_tick");
    }

    public static void setCrescendoReadyTick(ItemStack stack, long tick) {
        CustomData old = stack.get(DataComponents.CUSTOM_DATA);
        CompoundTag tag = old == null ? new CompoundTag() : old.copyTag();
        tag.putLong("crescendo_ready_tick", tick);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    /** Server game-time of the last successful use; -1 means legacy/never recorded. */
    public static long getLastUseTick(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null) return -1L;
        CompoundTag tag = data.copyTag();
        return tag.contains("last_weapon_use_tick", 4) ? tag.getLong("last_weapon_use_tick") : -1L;
    }

    public static void recordUse(ItemStack stack, long tick) {
        CustomData old = stack.get(DataComponents.CUSTOM_DATA);
        CompoundTag tag = old == null ? new CompoundTag() : old.copyTag();
        tag.putLong("last_weapon_use_tick", tick);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    private static void setInt(ItemStack stack, String key, int value) {
        CustomData old = stack.get(DataComponents.CUSTOM_DATA);
        CompoundTag tag = old == null ? new CompoundTag() : old.copyTag();
        tag.putInt(key, value);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    public static int getForm(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null) return 0;
        return Math.max(0, Math.min(9, data.copyTag().getInt("form")));
    }

    public static long getAnimationStart(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? -100000L : data.copyTag().getLong("animation_start");
    }

    public static int getAnimationMode(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? 0 : data.copyTag().getInt("animation_mode");
    }

    public static void setForm(ItemStack stack, int form) {
        setState(stack, form, null, 0L);
    }

    /** Server-synced animation beat; stage distinguishes repeated random forms. */
    public static int getFinisherStage(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? 0 : data.copyTag().getInt("finisher_stage");
    }

    public static long getFinisherBeatTick(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? -1L : data.copyTag().getLong("finisher_beat_tick");
    }

    public static void setFinisherBeat(ItemStack stack, int form, int stage, long now) {
        CustomData old = stack.get(DataComponents.CUSTOM_DATA);
        CompoundTag tag = old == null ? new CompoundTag() : old.copyTag();
        tag.putInt("form", form);
        tag.putInt("finisher_stage", stage);
        tag.putLong("finisher_beat_tick", now);
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(form));
        syncDisplayedName(stack, form);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    /** Display-only pose, never changes the canonical weapon form or its saved data. */
    public static void setAttackDisplay(ItemStack stack, int displayModel) {
        if (stack.getItem() instanceof OracleWeaponItem) {
            CustomModelData current = stack.get(DataComponents.CUSTOM_MODEL_DATA);
            if (current == null || current.value() != displayModel)
                stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(displayModel));
        }
    }

    public static void restoreAttackDisplay(ItemStack stack) {
        if (!(stack.getItem() instanceof OracleWeaponItem)) return;
        CustomModelData current = stack.get(DataComponents.CUSTOM_MODEL_DATA);
        if (current != null && (current.value() == 17 || current.value() == 19)) {
            stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(getForm(stack)));
        }
    }

    public static void clearFinisherBeat(ItemStack stack) {
        CustomData old = stack.get(DataComponents.CUSTOM_DATA);
        if (old == null) return;
        CompoundTag tag = old.copyTag();
        tag.remove("finisher_stage");
        tag.remove("finisher_beat_tick");
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    public static void setAnimation(ItemStack stack, int mode, long now) {
        setState(stack, -1, mode, now);
    }

    /** Sync the actual item name component used by hotbar and tooltip rendering.
     * ItemStack may already carry ITEM_NAME, bypassing our getName override;
     * preserving anvil CUSTOM_NAME is still handled by Minecraft itself. */
    /** Upgrade saved V0.10.66-68 ITEM_NAME components to the short white weapon title.
     * Only touches the generated ITEM_NAME, never an anvil CUSTOM_NAME; run at
     * most once per second so existing worlds update without morphing first. */
    public static void refreshDisplayedName(ItemStack stack) {
        if (!(stack.getItem() instanceof OracleWeaponItem)) return;
        int form = getForm(stack);
        Component expected = form >= 1 && form <= 9
                ? Component.translatable("form.oraclearsenal." + form)
                        .withStyle(ChatFormatting.WHITE)
                : Component.translatable("item.oraclearsenal.twin_serpent_staff")
                        .withStyle(ChatFormatting.WHITE);
        Component current = stack.get(DataComponents.ITEM_NAME);
        if (current != null && current.equals(expected)) return;
        stack.set(DataComponents.ITEM_NAME, expected);
    }

    private static void syncDisplayedName(ItemStack stack, int form) {
        if (form >= 1 && form <= 9) {
            stack.set(DataComponents.ITEM_NAME,
                    Component.translatable("form.oraclearsenal." + form)
                            .withStyle(ChatFormatting.WHITE));
        } else {
            stack.set(DataComponents.ITEM_NAME,
                    Component.translatable("item.oraclearsenal.twin_serpent_staff")
                            .withStyle(ChatFormatting.WHITE));
        }
    }

    private static void setState(ItemStack stack, int form, Integer mode, long tick) {
        CustomData old = stack.get(DataComponents.CUSTOM_DATA);
        CompoundTag tag = old == null ? new CompoundTag() : old.copyTag();
        if (form >= 0) {
            tag.putInt("form", form);
            stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(form));
            syncDisplayedName(stack, form);
        }
        if (mode != null) {
            tag.putInt("animation_mode", mode);
            tag.putLong("animation_start", tick);
        }
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }
}
