package io.github.oraclearsenal.client;

import io.github.oraclearsenal.OracleWeaponItem;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.minecraft.client.KeyMapping;
import com.mojang.blaze3d.platform.InputConstants;
import org.lwjgl.glfw.GLFW;

/** Vanilla command packet executes the special skill server-side; no custom network codec needed. */
public final class RienSkillKeybind {
    private RienSkillKeybind() { }

    public static void register() {
        KeyMapping crescendo = KeyBindingHelper.registerKeyBinding(new KeyMapping(
                "key.oraclearsenal.crescendo", InputConstants.Type.KEYSYM,
                GLFW.GLFW_KEY_V, "key.categories.oraclearsenal"));
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (crescendo.consumeClick()) {
                if (client.player == null || client.player.connection == null) continue;
                if (!(client.player.getMainHandItem().getItem() instanceof OracleWeaponItem)) continue;
                client.player.connection.sendCommand("rien crescendo");
            }
        });
    }
}
