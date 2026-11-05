package io.github.oraclearsenal;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import java.util.UUID;

/** A purely visual, short-lived silhouette at the departure location of a blink. */
public record BlinkAfterimagePayload(double x, double y, double z, float yaw, int form, int style, UUID actorId)
        implements CustomPacketPayload {
    public static final Type<BlinkAfterimagePayload> TYPE =
            new Type<>(OracleArsenal.id("blink_afterimage"));

    public static final StreamCodec<RegistryFriendlyByteBuf, BlinkAfterimagePayload> CODEC =
            StreamCodec.of((buf, value) -> {
                buf.writeDouble(value.x());
                buf.writeDouble(value.y());
                buf.writeDouble(value.z());
                buf.writeFloat(value.yaw());
                buf.writeVarInt(value.form());
                buf.writeVarInt(value.style());
                buf.writeUUID(value.actorId());
            }, buf -> new BlinkAfterimagePayload(
                    buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readFloat(),
                    buf.readVarInt(), buf.readVarInt(), buf.readUUID()));

    @Override
    public Type<? extends CustomPacketPayload> type() { return TYPE; }
}
