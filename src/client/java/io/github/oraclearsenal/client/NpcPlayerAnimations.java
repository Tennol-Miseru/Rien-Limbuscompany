package io.github.oraclearsenal.client;

import dev.kosmx.playerAnim.api.layered.KeyframeAnimationPlayer;
import dev.kosmx.playerAnim.core.data.KeyframeAnimation;
import dev.kosmx.playerAnim.impl.animation.AnimationApplier;
import dev.kosmx.playerAnim.minecraftApi.PlayerAnimationRegistry;
import io.github.oraclearsenal.OracleArsenal;
import io.github.oraclearsenal.RienNpcEntity;
import net.minecraft.client.model.PlayerModel;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Drives the Rien NPC with the same player-animator clips the player uses.
 *
 * <p>Player Animator attaches its layers to real players only, so a custom mob
 * never receives one. Instead the server stamps the clip name and start time on
 * the entity, and this class evaluates that keyframe file exactly like
 * {@code AnimationApplier} does for a player: read the transform for each part
 * at the current tick and write it onto the vanilla {@link PlayerModel} mesh.</p>
 */
public final class NpcPlayerAnimations {
    private static final Map<UUID, State> STATES = new HashMap<>();

    private NpcPlayerAnimations() { }

    /** Applies the NPC's current clip. Returns false when nothing is playing. */
    public static boolean apply(RienNpcEntity entity, PlayerModel<?> model) {
        String clip = entity.getAnimationClip();
        if (clip == null || clip.isEmpty()) return false;
        long start = entity.getAnimationStart();
        long age = entity.level().getGameTime() - start;
        if (age < 0 || age > 200) return false;
        KeyframeAnimation data = PlayerAnimationRegistry.getAnimation(OracleArsenal.id(clip))
                instanceof KeyframeAnimation animation ? animation : null;
        if (data == null) return false;

        UUID id = entity.getUUID();
        State state = STATES.get(id);
        if (state == null || !state.clip.equals(clip) || state.start != start) {
            state = new State(clip, start, new KeyframeAnimationPlayer(data));
            STATES.put(id, state);
        }
        int target = (int) age;
        // Advance one tick at a time; frames can be skipped, ticks cannot.
        while (state.player.getTick() < target && state.player.isActive()) {
            state.player.tick();
        }
        if (!state.player.isActive()) return false;

        AnimationApplier applier = new AnimationApplier(state.player);
        applier.updatePart("head", model.head);
        applier.updatePart("torso", model.body);
        applier.updatePart("rightArm", model.rightArm);
        applier.updatePart("leftArm", model.leftArm);
        applier.updatePart("rightLeg", model.rightLeg);
        applier.updatePart("leftLeg", model.leftLeg);

        model.hat.copyFrom(model.head);
        model.leftSleeve.copyFrom(model.leftArm);
        model.rightSleeve.copyFrom(model.rightArm);
        model.leftPants.copyFrom(model.leftLeg);
        model.rightPants.copyFrom(model.rightLeg);
        model.jacket.copyFrom(model.body);
        return true;
    }

    /** Drops cached animation state for entities that left the world. */
    public static void forget(UUID id) {
        STATES.remove(id);
    }

    private static final class State {
        final String clip;
        final long start;
        final KeyframeAnimationPlayer player;

        State(String clip, long start, KeyframeAnimationPlayer player) {
            this.clip = clip;
            this.start = start;
            this.player = player;
        }
    }
}
