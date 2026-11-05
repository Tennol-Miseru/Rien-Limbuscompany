package io.github.oraclearsenal;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Empty client hint for air swings: the server verifies the held item and cooldown. */
public record CombatSwingPayload() implements CustomPacketPayload {
    public static final Type<CombatSwingPayload> TYPE = new Type<>(OracleArsenal.id("ordinary_swing"));
    public static final StreamCodec<RegistryFriendlyByteBuf, CombatSwingPayload> CODEC =
            StreamCodec.unit(new CombatSwingPayload());

    @Override
    public Type<? extends CustomPacketPayload> type() { return TYPE; }
}
