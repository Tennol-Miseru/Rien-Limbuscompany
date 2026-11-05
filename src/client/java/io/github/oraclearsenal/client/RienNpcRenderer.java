package io.github.oraclearsenal.client;

import io.github.oraclearsenal.OracleArsenal;
import io.github.oraclearsenal.RienNpcEntity;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.ItemInHandLayer;
import net.minecraft.resources.ResourceLocation;

/** Real vanilla PlayerModel mesh and UV skin, not a scaled zombie model. */
public final class RienNpcRenderer extends MobRenderer<RienNpcEntity, RienNpcRenderer.RienPlayerModel> {
    // Phase one uses the original face texture, not an extra armor layer.
    // At the midpoint of the removal gesture we switch to scarred phase two.
    private static final ResourceLocation MASKED_SKIN = OracleArsenal.id("textures/entity/rien.png");
    private static final ResourceLocation UNMASKED_SKIN = OracleArsenal.id("textures/entity/rien_unmasked.png");

    public RienNpcRenderer(EntityRendererProvider.Context context) {
        super(context, new RienPlayerModel(context.bakeLayer(ModelLayers.PLAYER), false), .42f);
        this.addLayer(new ItemInHandLayer<>(this, context.getItemInHandRenderer()));
    }

    @Override
    public ResourceLocation getTextureLocation(RienNpcEntity entity) {
        return entity.hasRemovedMask() && entity.getMaskRemovalTicks() <= 14
                ? UNMASKED_SKIN : MASKED_SKIN;
    }

    /** A PlayerModel supports head turns, walking, sleeves, jacket and swinging arms. */
    public static final class RienPlayerModel extends PlayerModel<RienNpcEntity> {
        public RienPlayerModel(net.minecraft.client.model.geom.ModelPart root, boolean slim) {
            super(root, slim);
            this.hat.visible = true;
            this.jacket.visible = true;
            this.leftSleeve.visible = true;
            this.rightSleeve.visible = true;
            this.leftPants.visible = true;
            this.rightPants.visible = true;
        }

        @Override
        public void setupAnim(RienNpcEntity entity, float limbSwing, float limbSwingAmount,
                              float ageInTicks, float netHeadYaw, float headPitch) {
            super.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);
            int maskTicks = entity.getMaskRemovalTicks();
            int pagerTicks = entity.getPagerReadingTicks();
            if (maskTicks > 0) {
                // One-time hand-to-face gesture as he removes the porcelain half-mask.
                float progress = 1f - maskTicks / 28f;
                // Peak exactly when the equipped helmet passes to the offhand.
                float reach = progress <= .5f ? progress * 2f : (1f - progress) * 2f;
                float eased = reach * reach * (3f - 2f * reach);
                float raise = eased;
                this.leftArm.xRot = -2.05f * raise;
                this.leftArm.yRot = -.37f * raise;
                this.leftArm.zRot = -.29f * raise;
                this.head.xRot -= .13f * raise;
                this.rightArm.xRot = -.15f;
                this.leftSleeve.copyFrom(this.leftArm);
                this.rightSleeve.copyFrom(this.rightArm);
                return;
            }
            if (pagerTicks > 0) {
                // Hold pager near face and read it briefly, without mixing combat poses.
                float progress = 1f - pagerTicks / 36f;
                float raise = (float) Math.sin(Math.PI * Math.min(1f, progress * 1.5f));
                this.rightArm.xRot = -1.55f * raise;
                this.rightArm.yRot = -.2f * raise;
                this.leftArm.xRot = -.65f * raise;
                this.head.xRot += .2f * raise;
                this.rightSleeve.copyFrom(this.rightArm);
                this.leftSleeve.copyFrom(this.leftArm);
                return;
            }
            int windupTicks = entity.getUltimateWindupTicks();
            if (windupTicks > 0) {
                // Furioso telegraph: lift the actual prescript pager, read it,
                // then lower the arm before the first blink. Mask removal always
                // takes priority, and this pose never overlaps the nine strikes.
                float elapsed = (60f - windupTicks) / 60f;
                float lift = Math.min(1f, elapsed / .20f);
                lift = lift * lift * (3f - 2f * lift);
                float lower = Math.min(1f, (1f - elapsed) / .20f);
                lower = lower * lower * (3f - 2f * lower);
                float raised = lift * lower;
                this.rightArm.xRot = -1.65f * raised;
                this.rightArm.yRot = -.23f * raised;
                this.rightArm.zRot = -.10f * raised;
                this.leftArm.xRot = -.26f * raised;
                this.head.xRot += .16f * raised;
                this.rightSleeve.copyFrom(this.rightArm);
                this.leftSleeve.copyFrom(this.leftArm);
                return;
            }
            // Shared player clips drive both ordinary swings and the nine-beat
            // combo. The hand-written block below is only a fallback for a
            // missing clip file.
            if (NpcPlayerAnimations.apply(entity, this)) return;
            int stage = entity.getComboStage();
            if (stage != 0) {
                // Three pose families cycle throughout the nine strikes, with a more dramatic finisher.
                float beat = (float)Math.sin(ageInTicks * 1.65f);
                if (stage == 9) {
                    this.rightArm.xRot = -2.5f + beat * .18f;
                    this.leftArm.xRot = -1.35f;
                    this.rightArm.zRot = .25f;
                    this.body.yRot = .3f;
                } else if ((stage & 1) == 0) {
                    this.rightArm.xRot = -1.35f - beat * .6f;
                    this.rightArm.yRot = -.55f;
                    this.body.yRot = -.25f;
                } else {
                    this.rightArm.xRot = -2.0f + beat * .52f;
                    this.rightArm.yRot = .45f;
                    this.leftArm.xRot = -.65f;
                    this.body.yRot = .2f;
                }
                this.rightSleeve.copyFrom(this.rightArm);
                this.leftSleeve.copyFrom(this.leftArm);
            }
        }
    }
}
