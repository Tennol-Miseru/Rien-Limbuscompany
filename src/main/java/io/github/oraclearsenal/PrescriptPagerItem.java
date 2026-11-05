package io.github.oraclearsenal;

import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;

import java.util.List;
import java.util.Locale;

/**
 * An Index-inspired prescript pager. Messages are resource-pack-localized in
 * assets/oraclearsenal/lang/{zh_cn,en_us}.json; no client-side RNG or packet needed.
 */
public final class PrescriptPagerItem extends Item {
    /** Must equal the number of message.oraclearsenal.prescript.N localization keys. */
    public static final int PRESCRIPT_COUNT = 64;
    /** Extra optional red prescripts; never count toward the initial nine-trial progression. */
    public static final int SPECIAL_PRESCRIPT_COUNT = 14;
    private static final int RANDOM_POOL_SIZE = PRESCRIPT_COUNT + SPECIAL_PRESCRIPT_COUNT;
    private static final String LAST_INDEX = "pager_last_index";
    private static final String RECEIVE_TICK = "pager_receive_tick";

    public PrescriptPagerItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        // Minecraft sends the action to the server after client-side success.
        if (level.isClientSide) return InteractionResultHolder.success(stack);
        if (!(player instanceof ServerPlayer serverPlayer)) return InteractionResultHolder.pass(stack);
        if (serverPlayer.getCooldowns().isOnCooldown(this)) return InteractionResultHolder.success(stack);
        serverPlayer.getCooldowns().addCooldown(this, 20);
        // Owning the staff switches the pager from trial progression to a pure
        // random prescript reader. This also suppresses all trial-related text.
        if (PrescriptTrial.carryingStaff(serverPlayer)) {
            deliverRandom(serverPlayer, stack, level.getGameTime());
        } else {
            PrescriptTrial.receive(serverPlayer, stack, level.getGameTime());
        }
        // One short beep per accepted click, not once on each client and server.
        serverPlayer.serverLevel().playSound(null, serverPlayer.blockPosition(),
                RienSounds.PRESCRIPT_BEEP, SoundSource.PLAYERS, .52f, 1f);
        return InteractionResultHolder.success(stack);
    }

    /** Nine ordinary readings before the first trial, without special entries. */
    static void deliverOrdinary(ServerPlayer serverPlayer, ItemStack stack, long now) {
        deliver(serverPlayer, stack, now, PRESCRIPT_COUNT);
    }

    /** While a staff is carried, choose uniformly from all 78 messages. */
    static void deliverRandom(ServerPlayer serverPlayer, ItemStack stack, long now) {
        deliver(serverPlayer, stack, now, RANDOM_POOL_SIZE);
    }

    private static void deliver(ServerPlayer serverPlayer, ItemStack stack, long now, int poolSize) {
        CustomData old = stack.get(DataComponents.CUSTOM_DATA);
        CompoundTag tag = old == null ? new CompoundTag() : old.copyTag();
        int previous = tag.contains(LAST_INDEX) ? tag.getInt(LAST_INDEX) : -1;
        int index;
        // Prevent immediate repeats, including across an ordinary/special boundary.
        if (previous >= 0 && previous < poolSize && poolSize > 1) {
            index = serverPlayer.getRandom().nextInt(poolSize - 1);
            if (index >= previous) index++;
        } else {
            index = serverPlayer.getRandom().nextInt(poolSize);
        }
        tag.putInt(LAST_INDEX, index);
        tag.putLong(RECEIVE_TICK, now);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));

        boolean special = index >= PRESCRIPT_COUNT;
        String key = special
                ? "message.oraclearsenal.special_prescript." + (index - PRESCRIPT_COUNT)
                : "message.oraclearsenal.prescript." + index;
        String code = String.format(Locale.ROOT, "%04X", serverPlayer.getRandom().nextInt(65536));
        serverPlayer.sendSystemMessage(Component.empty()
                .append(Component.translatable("message.oraclearsenal.pager.header", code)
                        .withStyle(ChatFormatting.DARK_AQUA))
                .append(Component.translatable(key)
                        .withStyle(special ? ChatFormatting.RED : ChatFormatting.LIGHT_PURPLE)));
        serverPlayer.displayClientMessage(Component.translatable("message.oraclearsenal.pager.received")
                .withStyle(ChatFormatting.AQUA), true);
    }

    /** Synchronized ItemStack data: used for a small client-only receive animation. */
    public static long getReceiveTick(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? -100000L : data.copyTag().getLong(RECEIVE_TICK);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context,
                                List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.oraclearsenal.pager")
                .withStyle(ChatFormatting.AQUA));
        tooltip.add(Component.translatable("tooltip.oraclearsenal.pager.note")
                .withStyle(ChatFormatting.GRAY));
        super.appendHoverText(stack, context, tooltip, flag);
    }
}
