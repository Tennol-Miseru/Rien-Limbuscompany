package io.github.oraclearsenal.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import io.github.oraclearsenal.BlinkAfterimagePayload;
import io.github.oraclearsenal.HeartEffect;
import io.github.oraclearsenal.OracleArsenal;
import io.github.oraclearsenal.OracleWeaponItem;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.AABB;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Entity-free, particle-free silhouettes. Dark ghosts freeze the actual
 * weapon strike; gold ghosts mark movement while Heart is active. */
public final class BlinkAfterimageRenderer {
    private static final ResourceLocation SILHOUETTE =
            OracleArsenal.id("textures/entity/blink_silhouette.png");
    private static final ResourceLocation GOLD_SILHOUETTE =
            OracleArsenal.id("textures/entity/heart_afterimage.png");
    private static final ArrayDeque<Ghost> BLACK = new ArrayDeque<>();
    private static final ArrayDeque<Ghost> GOLD = new ArrayDeque<>();
    private static final Map<UUID, Track> TRACKS = new HashMap<>();
    private static final int MAX_BLACK = 18;
    private static final int MAX_GOLD = 22;
    private static final int BLACK_TICKS = 12; // .6 seconds
    private static final int GOLD_TICKS = 5; // .25 seconds
    private static ClientLevel trackedLevel;
    private static PlayerModel<LivingEntity> model;

    private BlinkAfterimageRenderer() { }

    public static void register() {
        ClientPlayNetworking.registerGlobalReceiver(BlinkAfterimagePayload.TYPE, (packet, context) -> {
            Minecraft minecraft = context.client();
            if (minecraft.level == null) return;
            if (minecraft.level != trackedLevel) reset(minecraft.level);
            // V-key ghosts use one shared origin and one frozen weapon pose for
            // both dark and gold layers. Drop any separately sampled gold trail
            // left over from movement just before the cinematic blink.
            if (packet.style() == 2) GOLD.removeIf(g -> g.actorId.equals(packet.actorId()));
            append(BLACK, new Ghost(new Vec3(packet.x(), packet.y(), packet.z()),
                    packet.yaw(), minecraft.level.getGameTime(), packet.form(),
                    packet.style(), packet.actorId()), MAX_BLACK);
        });
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (client.level != trackedLevel) reset(client.level);
            if (trackedLevel == null) return;
            long now = trackedLevel.getGameTime();
            BLACK.removeIf(ghost -> now < ghost.createdTick || now - ghost.createdTick >= BLACK_TICKS);
            GOLD.removeIf(ghost -> now < ghost.createdTick || now - ghost.createdTick >= GOLD_TICKS);
            trackHeartMovement(client, now);
        });
        WorldRenderEvents.AFTER_ENTITIES.register(context -> {
            if (context.world() != trackedLevel || context.matrixStack() == null ||
                    context.consumers() == null || (BLACK.isEmpty() && GOLD.isEmpty())) return;
            Minecraft minecraft = Minecraft.getInstance();
            if (model == null) {
                model = new PlayerModel<>(minecraft.getEntityModels().bakeLayer(ModelLayers.PLAYER), false);
                // Keep the silhouette clean, no secondary jacket/sleeve layers.
                model.hat.visible = false;
                model.jacket.visible = false;
                model.leftSleeve.visible = false;
                model.rightSleeve.visible = false;
                model.leftPants.visible = false;
                model.rightPants.visible = false;
            }
            PoseStack stack = context.matrixStack();
            MultiBufferSource buffers = context.consumers();
            Vec3 camera = context.camera().getPosition();
            double partial = context.tickCounter().getGameTimeDeltaPartialTick(false);
            long now = trackedLevel.getGameTime();
            // Don't render our own afterimages over the camera in normal first
            // person. V-key's detached cinematic camera may still see the
            // combined black/gold ghost at the blink origin.
            boolean hideOwnInFirstPerson = minecraft.options.getCameraType().isFirstPerson()
                    && !LacrimosaCamera.active();
            UUID localId = minecraft.player == null ? null : minecraft.player.getUUID();
            boolean backpedaling = localId != null
                    && TRACKS.containsKey(localId) && TRACKS.get(localId).backpedaling;
            for (Ghost ghost : GOLD) {
                if (ghost.actorId.equals(localId)
                        && (hideOwnInFirstPerson || backpedaling)) continue;
                draw(stack, buffers, camera, ghost, now, partial, GOLD_TICKS, false);
            }
            for (Ghost ghost : BLACK) {
                if (ghost.actorId.equals(localId) && hideOwnInFirstPerson) continue;
                draw(stack, buffers, camera, ghost, now, partial, BLACK_TICKS, true);
            }
        });
    }

    private static void trackHeartMovement(Minecraft client, long now) {
        if (client.player == null || now % 2 != 0) return;
        // Client-side sampling removes per-tick server broadcasts. Only
        // nearby living entities with Heart participate (including Rien NPC).
        AABB nearby = client.player.getBoundingBox().inflate(24.0);
        for (LivingEntity actor : trackedLevel.getEntitiesOfClass(LivingEntity.class, nearby,
                e -> e.isAlive() && !e.isInvisible() && e.hasEffect(HeartEffect.HEART))) {
            UUID id = actor.getUUID();
            Vec3 pos = actor.position();
            Track old = TRACKS.get(id);
            Vec3 displacement = old == null ? Vec3.ZERO : pos.subtract(old.position);
            Vec3 heading = actor.getLookAngle().multiply(1, 0, 1);
            // In third person, historical snapshots from walking BACKWARD can
            // be projected straight over the real player. Avoid generating
            // that overlapping gold ghost; also suppress recently sampled ones
            // while backpedaling (the render loop checks this flag).
            boolean backwards = old != null && displacement.dot(heading) < -0.025;
            TRACKS.put(id, new Track(pos, now, backwards));
            if (old == null || now - old.tick > 8) continue;
            double distanceSquared = displacement.lengthSqr();
            if (distanceSquared < .20 * .20 || distanceSquared > 2.2 * 2.2) continue;
            // While V is active, its black flash already carries a gold layer
            // at the SAME position, orientation and weapon-attack frame. Do
            // not additionally leave misaligned moving golden silhouettes.
            if (actor.getMainHandItem().getItem() instanceof OracleWeaponItem
                    && OracleWeaponItem.getAnimationMode(actor.getMainHandItem()) == 4) continue;
            if (actor == client.player) {
                if (backwards) continue;
                // Suppress self trails in first person at the SOURCE, not just
                // when drawing, so switching camera cannot reveal queued
                // ghosts that were never meant to be visible.
                if (client.options.getCameraType().isFirstPerson()
                        && !LacrimosaCamera.active()) continue;
            }
            append(GOLD, new Ghost(old.position, actor.getYRot(), now, 0, 0, id), MAX_GOLD);
        }
        TRACKS.entrySet().removeIf(entry -> now - entry.getValue().tick > 12);
    }

    private static void draw(PoseStack pose, MultiBufferSource buffer, Vec3 camera,
                             Ghost ghost, long now, double partial, int duration,
                             boolean black) {
        double age = now - ghost.createdTick + partial;
        if (age < 0 || age >= duration) return;
        float fade = (float)Math.pow(1.0 - age / duration, black ? 1.25 : 1.65);
        pose.pushPose();
        pose.translate(ghost.origin.x - camera.x, ghost.origin.y - camera.y,
                ghost.origin.z - camera.z);
        pose.mulPose(Axis.YP.rotationDegrees(180.0f - ghost.yaw));
        pose.scale(-1.0f, -1.0f, 1.0f);
        pose.translate(0, -1.501f, 0);
        neutral();
        if (black || ghost.style == 2) {
            WeaponGhostPose.apply(model, ghost.form, ghost.style);
        } else {
            float stride = (float)Math.sin(ghost.createdTick * .65) * .36f;
            model.rightLeg.xRot = stride;
            model.leftLeg.xRot = -stride;
            model.rightArm.xRot = -stride * .55f;
            model.leftArm.xRot = stride * .55f;
        }
        if (black && ghost.style == 2) {
            // Layer the gold aura *on the exact same frozen weapon pose and
            // blink location*. The 2% enlarged gold silhouette acts as a thin
            // edge glow instead of another separately placed human figure.
            pose.pushPose();
            pose.scale(1.025f, 1.025f, 1.025f);
            renderTint(pose, buffer, GOLD_SILHOUETTE, .31f * fade, 0xFFD16B);
            pose.popPose();
            renderTint(pose, buffer, SILHOUETTE, .64f * fade, 0x0A0C16);
        } else {
            renderTint(pose, buffer, black ? SILHOUETTE : GOLD_SILHOUETTE,
                    (black ? .72f : .24f) * fade,
                    black ? 0x0A0C16 : 0xFFD16B);
        }
        pose.popPose();
    }

    private static void renderTint(PoseStack pose, MultiBufferSource buffer,
                                   ResourceLocation texture, float opacity, int rgb) {
        int alpha = Math.max(0, Math.min(255, (int)(opacity * 255)));
        if (alpha < 5) return;
        model.renderToBuffer(pose, buffer.getBuffer(RenderType.entityTranslucent(texture)),
                LightTexture.FULL_BRIGHT, OverlayTexture.NO_OVERLAY,
                (alpha << 24) | rgb);
    }

    private static void neutral() {
        // Explicitly force adult-size, default standing proportions. Without
        // this, the cached model can retain young/crouching state and render a
        // noticeably undersized afterimage.
        model.young = false;
        model.crouching = false;
        model.riding = false;
        model.attackTime = 0.0f;
        model.head.xRot = model.head.yRot = model.head.zRot = 0;
        model.hat.xRot = model.hat.yRot = model.hat.zRot = 0;
        model.body.xRot = model.body.yRot = model.body.zRot = 0;
        model.rightArm.xRot = model.rightArm.yRot = model.rightArm.zRot = 0;
        model.leftArm.xRot = model.leftArm.yRot = model.leftArm.zRot = 0;
        model.rightLeg.xRot = model.rightLeg.yRot = model.rightLeg.zRot = 0;
        model.leftLeg.xRot = model.leftLeg.yRot = model.leftLeg.zRot = 0;
    }

    private static void append(ArrayDeque<Ghost> array, Ghost ghost, int max) {
        if (array.size() >= max) array.removeFirst();
        array.addLast(ghost);
    }

    private static void reset(ClientLevel world) {
        BLACK.clear();
        GOLD.clear();
        TRACKS.clear();
        trackedLevel = world;
    }

    private record Ghost(Vec3 origin, float yaw, long createdTick, int form,
                         int style, UUID actorId) { }
    private record Track(Vec3 position, long tick, boolean backpedaling) { }
}
