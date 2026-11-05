package io.github.oraclearsenal.client;

import dev.kosmx.playerAnim.api.IPlayable;
import dev.kosmx.playerAnim.api.firstPerson.FirstPersonConfiguration;
import dev.kosmx.playerAnim.api.firstPerson.FirstPersonMode;
import dev.kosmx.playerAnim.api.layered.IAnimation;
import dev.kosmx.playerAnim.api.layered.KeyframeAnimationPlayer;
import dev.kosmx.playerAnim.api.layered.ModifierLayer;
import dev.kosmx.playerAnim.api.layered.modifier.AbstractFadeModifier;
import dev.kosmx.playerAnim.core.data.KeyframeAnimation;
import dev.kosmx.playerAnim.core.util.Ease;
import dev.kosmx.playerAnim.minecraftApi.PlayerAnimationAccess;
import dev.kosmx.playerAnim.minecraftApi.PlayerAnimationFactory;
import dev.kosmx.playerAnim.minecraftApi.PlayerAnimationRegistry;
import io.github.oraclearsenal.OracleArsenal;
import io.github.oraclearsenal.CombatSwingPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import io.github.oraclearsenal.OracleWeaponItem;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Server-selected weapon-specific animation clips for both finishers.
 * A synced beat index changes with every attack, even if the same form reappears.
 * Player Animator interpolates each pose; server owns random choice and hit windows.
 */
public final class OraclePlayerAnimations {
    private static final net.minecraft.resources.ResourceLocation LAYER_ID = OracleArsenal.id("combat_layer");
    private static final String[] ORDINARY_BY_FORM = {
            "", "attack_form_1", "attack_form_2", "attack_form_3",
            "attack_form_4", "attack_form_5", "attack_form_6",
            "attack_form_7", "attack_form_8", "attack_form_9"
    };
    // Each strike is a full-body move: knees, torso turn, root dip, arms and weapon.
    // Weapon changes occur on the server eight ticks apart; contact is at tick +3.
    private static final String[] FINISHER_BY_FORM = {
            "", "crescendo_handaxe_front", "crescendo_awl_stab",
            "crescendo_greatsword_cleave", "crescendo_rapier_uppercut",
            "crescendo_hammer_front", "crescendo_sword_down",
            "crescendo_lance_triple", "crescendo_long_whip_snap", "furioso_final_pose"
    };
    // Lacrimosa (V) has independent, more expansive 8-tick full-body strikes.
    // Replica (Shift+RMB) deliberately keeps the original animation set.
    // Form nine uses one uninterrupted strike-to-pose clip (32 ticks total).
    private static final String[] LACRIMOSA_BY_FORM = {
            "", "lacrimosa_form_1", "lacrimosa_form_2", "lacrimosa_form_3",
            "lacrimosa_form_4", "lacrimosa_form_5", "lacrimosa_form_6",
            "lacrimosa_form_7", "lacrimosa_form_8", "furioso_final_pose"
    };
    private static final Map<UUID, String> PLAYED = new HashMap<>();
    private static final Map<UUID, Float> PREVIOUS_SWING = new HashMap<>();
    private static final Map<UUID, Boolean> WAS_SWINGING = new HashMap<>();
    private static final Map<UUID, Long> LOCAL_SWING_TICK = new HashMap<>();

    private OraclePlayerAnimations() { }

    public static void register() {
        PlayerAnimationFactory.ANIMATION_DATA_FACTORY.registerFactory(
                LAYER_ID, 210, player -> new ModifierLayer<IAnimation>());
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (client.level == null) {
                PLAYED.clear();
                PREVIOUS_SWING.clear();
                WAS_SWINGING.clear();
                LOCAL_SWING_TICK.clear();
                return;
            }
            Set<UUID> present = new HashSet<>();
            for (Player p : client.level.players()) {
                if (!(p instanceof AbstractClientPlayer player)) continue;
                present.add(player.getUUID());
                tickPlayer(player, client.level.getGameTime());
            }
            PLAYED.keySet().removeIf(id -> !present.contains(id));
            PREVIOUS_SWING.keySet().removeIf(id -> !present.contains(id));
            WAS_SWINGING.keySet().removeIf(id -> !present.contains(id));
            LOCAL_SWING_TICK.keySet().removeIf(id -> !present.contains(id));
        });
    }

    @SuppressWarnings("unchecked")
    private static void tickPlayer(AbstractClientPlayer player, long now) {
        var animation = PlayerAnimationAccess.getPlayerAssociatedData(player).get(LAYER_ID);
        if (!(animation instanceof ModifierLayer<?>)) return;
        ModifierLayer<IAnimation> layer = (ModifierLayer<IAnimation>) animation;
        ItemStack stack = player.getMainHandItem();
        if (!(stack.getItem() instanceof OracleWeaponItem)) {
            stop(player, layer);
            return;
        }
        int mode = OracleWeaponItem.getAnimationMode(stack);
        long start = OracleWeaponItem.getAnimationStart(stack);
        long age = now - start;
        UUID playerId = player.getUUID();
        // Minecraft sends arm-swing state for air hits and mining as well.
        // No server hit is required; only the pose is client-side.
        float swing = player.getAttackAnim(0.0f);
        float oldSwing = PREVIOUS_SWING.getOrDefault(playerId, 0f);
        boolean wasSwinging = WAS_SWINGING.getOrDefault(playerId, false);
        boolean freshSwing = player.swinging && (!wasSwinging || swing + .15f < oldSwing);
        PREVIOUS_SWING.put(playerId, swing);
        WAS_SWINGING.put(playerId, player.swinging);
        boolean specialActive = (mode == 2 || mode == 4) && age >= 0 && age < (mode == 2 ? 104 : 108);
        boolean blinkActive = mode == 1 && age >= 0 && age < 12;
        if (OracleWeaponItem.getForm(stack) == 0 && !specialActive && !blinkActive) {
            stop(player, layer);
            return; // The unmanifested staff is not a nine-form weapon.
        }
        if (freshSwing && !specialActive && !blinkActive) {
            LOCAL_SWING_TICK.put(playerId, now);
            // Attack-air has no vanilla server hit callback. This sends intent
            // only, never movement coordinates or untrusted damage information.
            if (player == Minecraft.getInstance().player &&
                    ClientPlayNetworking.canSend(CombatSwingPayload.TYPE)) {
                ClientPlayNetworking.send(new CombatSwingPayload());
            }
        }
        String clip;
        long fallbackStart = LOCAL_SWING_TICK.getOrDefault(playerId, Long.MIN_VALUE / 2);
        long fallbackAge = now - fallbackStart;
        int ordinaryTicks = 12;
        boolean ordinaryServer = mode == 3 && age >= 0 && age < ordinaryTicks;
        int stage = 0;
        if (specialActive) {
            stage = OracleWeaponItem.getFinisherStage(stack);
            if (stage > 0 && stage <= 9) {
                int form = OracleWeaponItem.getForm(stack);
                // Always display the form chosen by the SERVER, not a local guess.
                int selected = Math.max(1, Math.min(9, form));
                // V-key gets eight separate, energetic weapon styles; the
                // ordinary nine-blink retains its previous clips. The ninth
                // beat uses exactly ONE clip from entry to release; never
                // start a competing hold layer at the end of the strike.
                if (stage == 9) {
                    clip = "furioso_final_pose";
                } else {
                    clip = mode == 4 ? LACRIMOSA_BY_FORM[selected]
                            : FINISHER_BY_FORM[selected];
                }
            } else {
                clip = mode == 4 ? "lacrimosa_opening" : "replica_spectral_full";
            }
        } else if (blinkActive) {
            clip = "blink_draw";
        } else if (ordinaryServer) {
            int form = OracleWeaponItem.getForm(stack);
            clip = ORDINARY_BY_FORM[Math.max(1, Math.min(9, form))];
            // The local attack animation already started when the arm swung.
            // Server NBT normally arrives a tick later: don't restart the same
            // swing and cause a visible mid-attack pop when it is confirmed.
            if (fallbackAge >= 0 && fallbackAge < 12 && Math.abs(start - fallbackStart) <= 5) {
                start = fallbackStart;
            }
        } else if (fallbackAge >= 0 && fallbackAge < ordinaryTicks) {
            // Air / block swings remain animated even when the stored animation mode
            // is still 1 (old teleport) or 2/4 (finished ultimate).
            clip = ORDINARY_BY_FORM[Math.max(1, Math.min(9, OracleWeaponItem.getForm(stack)))];
            start = fallbackStart;
            mode = 3;
        } else {
            stop(player, layer);
            return;
        }
        // Stage is part of the key: repeating one form later STILL restarts its strike.
        String key = mode + ":" + start + ":" + stage + ":" + clip;
        if (key.equals(PLAYED.get(player.getUUID()))) return;
        IPlayable playable = PlayerAnimationRegistry.getAnimation(OracleArsenal.id(clip));
        if (playable == null) {
            OracleArsenal.LOGGER.error("Missing player animation: {}. Check the player_animations resource folder.", clip);
            // Do not silently keep the previous pose if a clip is absent.
            stop(player, layer);
            return;
        }
        IAnimation running;
        if (playable instanceof KeyframeAnimation keyframe) {
            KeyframeAnimationPlayer instance = new KeyframeAnimationPlayer(keyframe);
            if (mode == 4) {
                // Cinematic CA shows full third-person body; keep Replica first-person weapons visible.
                instance.setFirstPersonMode(FirstPersonMode.THIRD_PERSON_MODEL);
                instance.setFirstPersonConfiguration(new FirstPersonConfiguration()
                        .setShowRightArm(true).setShowLeftArm(true)
                        .setShowRightItem(true).setShowLeftItem(true));
            }
            running = instance;
        } else {
            running = playable.playAnimation();
        }
        // Eight-tick special beats must reach their weapon-specific contact frames.
        // A two-tick fade loses a quarter of each pose; the final pose is slower.
        int blend = (mode == 2 || mode == 4) && stage > 0 ? 1
                : mode == 3 ? 2 : 3;
        layer.replaceAnimationWithFade(
                AbstractFadeModifier.standardFadeIn(blend, Ease.INOUTSINE), running);
        PLAYED.put(player.getUUID(), key);
    }

    /** Age of the latest observed arm swing (including whiffs and block attacks). */
    public static double getOrdinarySwingAge(AbstractClientPlayer player, double clock) {
        long started = LOCAL_SWING_TICK.getOrDefault(player.getUUID(), Long.MIN_VALUE / 2);
        return clock - started;
    }

    private static void stop(AbstractClientPlayer player, ModifierLayer<IAnimation> layer) {
        String previous = PLAYED.remove(player.getUUID());
        if (previous != null) {
            int exitTicks = (previous.startsWith("2:") || previous.startsWith("4:")) ? 2 : 4;
            layer.replaceAnimationWithFade(
                    AbstractFadeModifier.standardFadeIn(exitTicks, Ease.INOUTSINE), null);
        }
    }
}
