package io.github.oraclearsenal;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

/** Server-owned departure silhouettes; never creates a real entity or particles. */
public final class RienAfterimages {
    private RienAfterimages() { }

    public static void register() {
        PayloadTypeRegistry.playS2C().register(BlinkAfterimagePayload.TYPE, BlinkAfterimagePayload.CODEC);
    }

    public static void departure(ServerLevel level, LivingEntity actor, Vec3 position) {
        int form = actor instanceof RienNpcEntity rien ? rien.getCurrentForm()
                : actor.getMainHandItem().getItem() instanceof OracleWeaponItem
                ? OracleWeaponItem.getForm(actor.getMainHandItem()) : 0;
        int style = 0;
        if (actor instanceof ServerPlayer player &&
                player.getMainHandItem().getItem() instanceof OracleWeaponItem) {
            int mode = OracleWeaponItem.getAnimationMode(player.getMainHandItem());
            style = mode == 4 ? 2 : mode == 2 ? 1 : 0;
        } else if (actor instanceof RienNpcEntity rien && rien.getComboStage() > 0) {
            style = 1;
        }
        departure(level, actor, position, form, style);
    }

    /** Use the weapon of THIS beat, not the form left over from the previous beat. */
    public static void departure(ServerLevel level, LivingEntity actor, Vec3 position,
                                 int form, int style) {
        BlinkAfterimagePayload packet = new BlinkAfterimagePayload(
                position.x, position.y, position.z, actor.getYRot(),
                Math.max(0, Math.min(9, form)), Math.max(0, Math.min(2, style)),
                actor.getUUID());
        // Send from the origin BEFORE the teleport. This includes the caster and
        // nearby observers, and keeps the silhouette in the correct dimension.
        for (ServerPlayer observer : PlayerLookup.around(level, position, 64.0)) {
            if (ServerPlayNetworking.canSend(observer, BlinkAfterimagePayload.TYPE)) {
                ServerPlayNetworking.send(observer, packet);
            }
        }
    }
}
