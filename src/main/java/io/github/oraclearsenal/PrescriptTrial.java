package io.github.oraclearsenal;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;

import java.util.UUID;

/** A player-owned, nonlethal Rien trial in the Overworld, repeatable after weapon loss. */
public final class PrescriptTrial {
    private static final int REQUIRED_PRESCRIPTS = 9;
    private static final double ARRIVAL_RADIUS = 24.0;

    private PrescriptTrial() { }

    public static void receive(ServerPlayer player, ItemStack pager, long now) {
        PrescriptTrialAccess progress = (PrescriptTrialAccess) player;
        int phase = progress.oraclearsenal$getTrialPhase();
        // An issued challenge cannot be started while a Twin Serpent Staff is
        // carried. Check every direct inventory slot, not only the selected hand.
        if (phase >= 1 && phase <= 2) {
            if (carryingStaff(player)) {
                tell(player, "message.oraclearsenal.trial.staff_carried");
                return;
            }
            showLocation(player);
            return;
        }
        if (phase == 0 && progress.oraclearsenal$getPrescriptCount() < REQUIRED_PRESCRIPTS) {
            PrescriptPagerItem.deliverOrdinary(player, pager, now);
            progress.oraclearsenal$setPrescriptCount(progress.oraclearsenal$getPrescriptCount() + 1);
            player.sendSystemMessage(Component.translatable("message.oraclearsenal.trial.progress",
                    progress.oraclearsenal$getPrescriptCount(), REQUIRED_PRESCRIPTS)
                    .withStyle(ChatFormatting.GRAY));
            return;
        }
        // Both the first special instruction and any repeat challenge require
        // the player to have no staff in inventory, armor or offhand slots.
        // Phase 3 means the first trial was completed, not permanently locked.
        if (carryingStaff(player)) {
            tell(player, "message.oraclearsenal.trial.staff_carried");
            return;
        }
        if (!player.serverLevel().dimension().equals(Level.OVERWORLD)) {
            tell(player, "message.oraclearsenal.trial.overworld");
            return;
        }
        BlockPos site = locate(player);
        if (site == null) {
            tell(player, "message.oraclearsenal.trial.no_site");
            return;
        }
        progress.oraclearsenal$setTrialPosition(site.getX(), site.getY(), site.getZ());
        progress.oraclearsenal$setTrialPhase(1);
        progress.oraclearsenal$setTrialBossId(null);
        player.sendSystemMessage(Component.translatable(phase == 3
                ? "message.oraclearsenal.trial.special_repeat"
                : "message.oraclearsenal.trial.special")
                .withStyle(ChatFormatting.GOLD));
        showLocation(player);
    }

    /** Item identity survives every morph/CMD variation of the Twin Serpent Staff.
     *  Inventory#getContainerSize includes the hotbar, main inventory, armor
     *  and offhand slots. Deliberately excludes remote storage/ender chests. */
    static boolean carryingStaff(ServerPlayer player) {
        for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
            if (player.getInventory().getItem(slot).is(OracleArsenal.TWIN_SERPENT_STAFF))
                return true;
        }
        return false;
    }

    private static void tell(ServerPlayer player, String key) {
        player.sendSystemMessage(Component.translatable(key).withStyle(ChatFormatting.AQUA));
    }

    public static void showLocation(ServerPlayer player) {
        PrescriptTrialAccess state = (PrescriptTrialAccess) player;
        player.sendSystemMessage(Component.translatable("message.oraclearsenal.trial.location",
                state.oraclearsenal$getTrialX(), state.oraclearsenal$getTrialY(),
                state.oraclearsenal$getTrialZ()).withStyle(ChatFormatting.GOLD));
        if (state.oraclearsenal$getTrialPhase() == 2)
            tell(player, "message.oraclearsenal.trial.in_progress");
    }

    private static BlockPos locate(ServerPlayer player) {
        ServerLevel level = player.serverLevel();
        for (int i = 0; i < 12; i++) {
            double angle = player.getRandom().nextDouble() * Math.PI * 2;
            int radius = 112 + player.getRandom().nextInt(97);
            int x = player.getBlockX() + (int) Math.round(Math.cos(angle) * radius);
            int z = player.getBlockZ() + (int) Math.round(Math.sin(angle) * radius);
            BlockPos site = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                    new BlockPos(x, 0, z));
            if (site.getY() < level.getSeaLevel() || !level.getWorldBorder().isWithinBounds(site)) continue;
            BlockPos below = site.below();
            if (!level.getFluidState(site).isEmpty() || !level.getFluidState(below).isEmpty()
                    || !level.getBlockState(below).isSolidRender(level, below)) continue;
            AABB box = new AABB(x + .2, site.getY(), z + .2,
                    x + .8, site.getY() + 1.8, z + .8);
            if (level.noCollision(box)) return site;
        }
        return null;
    }

    /** Called once per second; the boss only spawns after its chunk is near a player. */
    public static void tick(ServerPlayer player) {
        PrescriptTrialAccess state = (PrescriptTrialAccess) player;
        int phase = state.oraclearsenal$getTrialPhase();
        if (phase != 1 && phase != 2) return;
        if (!player.serverLevel().dimension().equals(Level.OVERWORLD)) return;
        // Do not spawn or re-spawn a boss if a staff was acquired after the
        // instruction was issued. An existing phase-2 boss is not despawned;
        // the completion guard below still prevents a duplicate reward.
        if (carryingStaff(player)) return;
        BlockPos site = new BlockPos(state.oraclearsenal$getTrialX(),
                state.oraclearsenal$getTrialY(), state.oraclearsenal$getTrialZ());
        if (player.distanceToSqr(site.getX() + .5, site.getY(), site.getZ() + .5)
                > ARRIVAL_RADIUS * ARRIVAL_RADIUS) return;
        ServerLevel level = player.serverLevel();
        UUID bossId = state.oraclearsenal$getTrialBossId();
        Entity existing = bossId == null ? null : level.getEntity(bossId);
        if (existing instanceof RienNpcEntity boss && boss.isAlive()) return;
        // A missing entity after a reload or admin removal may be challenged again.
        if (!level.noCollision(new AABB(site.getX() + .2, site.getY(), site.getZ() + .2,
                site.getX() + .8, site.getY() + 1.8, site.getZ() + .8))) return;
        RienNpcEntity boss = OracleArsenal.RIEN_NPC.create(level);
        if (boss == null) return;
        boss.moveTo(site.getX() + .5, site.getY(), site.getZ() + .5, player.getYRot() + 180f, 0f);
        boss.assignTrialOwner(player);
        if (!level.addFreshEntity(boss)) return;
        state.oraclearsenal$setTrialBossId(boss.getUUID());
        state.oraclearsenal$setTrialPhase(2);
        player.sendSystemMessage(Component.translatable("message.oraclearsenal.trial.start")
                .withStyle(ChatFormatting.RED));
    }

    public static void completed(ServerPlayer player, RienNpcEntity boss) {
        PrescriptTrialAccess state = (PrescriptTrialAccess) player;
        if (state.oraclearsenal$getTrialPhase() != 2
                || !boss.getUUID().equals(state.oraclearsenal$getTrialBossId())) return;
        state.oraclearsenal$setTrialPhase(3); // Write first; one payout per boss.
        state.oraclearsenal$setTrialBossId(null);
        // Another staff may have been received while this boss was active.
        // Such a win completes the encounter without granting another staff.
        if (carryingStaff(player)) {
            tell(player, "message.oraclearsenal.trial.reward_already_owned");
            return;
        }
        ItemStack weapon = new ItemStack(OracleArsenal.TWIN_SERPENT_STAFF);
        if (!player.getInventory().add(weapon)) player.drop(weapon, false);
        player.sendSystemMessage(Component.translatable("message.oraclearsenal.trial.victory")
                .withStyle(ChatFormatting.GOLD));
    }
}
