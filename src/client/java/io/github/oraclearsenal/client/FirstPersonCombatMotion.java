package io.github.oraclearsenal.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;

/**
 * First-person-only choreography for the nine weapon forms.
 *
 * The vanilla hand renderer draws the real hand AND held item underneath this
 * pose stack. Each clip has anticipation, wind-up, contact, follow-through and
 * recovery; Catmull-Rom interpolation avoids per-tick snapping. This is a visual
 * layer only: hit detection and finisher timing are controlled by the server.
 *
 * A frame has normalized time, XYZ translation (blocks), XYZ Euler rotations
 * (degrees). Rotations are intentionally modest on long weapons to limit
 * first-person camera clipping. Form-specific third-person animations are not
 * modified by this class.
 */
public final class FirstPersonCombatMotion {
    private FirstPersonCombatMotion() { }

    // 6 frames for each of nine different attacks. Time values in [0, 1].
    // Curves are smooth; these are authored poses, NOT random per-render swings.
    private static final float[][][] STRIKES = {
        null,
        // 1: hand axe — pull across the body, chop sharply, settle low.
        {f(0f,     0, 0, 0, 0, 0, 0),
         f(.17f,  .13f,-.05f,.13f, -18,-30, 30),
         f(.35f,  .25f,.10f,.16f, -38,-45, 47),
         f(.51f, -.21f,-.19f,-.24f, 46,28,-66),
         f(.73f, -.11f,-.17f,-.17f, 29,15,-37),
         f(1f,    0,0,0, 0,0,0)},
        // 2: awl — compact low guard, a precise forward stab, recoil.
        {f(0f,     0,0,0, 0,0,0),
         f(.18f, -.11f,-.09f,.20f, 24,-18,-12),
         f(.34f, -.13f,-.10f,.24f, 30,-21,-14),
         f(.48f, .08f,.04f,-.47f, -55,4,6),
         f(.70f, .05f,.02f,-.23f, -34,3,4),
         f(1f,    0,0,0,0,0,0)},
        // 3: greatsword — shoulder preparation, sweeping cross-body cut.
        {f(0f,     0,0,0, 0,0,0),
         f(.20f,  .13f,.13f,.20f, -45,-24,44),
         f(.39f,  .20f,.19f,.19f, -64,-40,61),
         f(.57f, -.28f,-.16f,-.29f, 22,48,-66),
         f(.78f, -.18f,-.10f,-.17f, 14,29,-35),
         f(1f,    0,0,0,0,0,0)},
        // 4: rapier — retreating low guard -> ascending thrust, then raised tip.
        // Vertical blade travel follows the actual server-side launch contact.
        {f(0f,     0,0,0,0,0,0),
         f(.15f, .11f,-.16f,.17f, 22,23,13),
         f(.32f, .14f,-.20f,.24f, 31,25,19),
         f(.48f, -.05f,.24f,-.47f, -115,3,-8),
         f(.67f, -.02f,.19f,-.29f, -101,4,-2),
         f(1f,    0,0,0,0,0,0)},
        // 5: hammer — heavy overhead lift and forceful downward impact.
        {f(0f,    0,0,0,0,0,0),
         f(.23f, -.08f,.17f,.20f, -55,-17,-19),
         f(.44f, -.11f,.28f,.29f, -87,-26,-22),
         f(.62f, .06f,-.28f,-.36f, 54,21,29),
         f(.82f, .04f,-.16f,-.21f, 26,9,15),
         f(1f,   0,0,0,0,0,0)},
        // 6: colossal greatsword — exaggerated two-stage heavy cleave.
        {f(0f,    0,0,0,0,0,0),
         f(.24f, .13f,.22f,.20f, -57,-22,33),
         f(.45f, .20f,.30f,.28f, -83,-32,46),
         f(.66f, -.20f,-.32f,-.37f, 65,30,-57),
         f(.86f, -.12f,-.16f,-.19f, 22,12,-22),
         f(1f,   0,0,0,0,0,0)},
        // 7: knight lance — brace low, then project the actual held lance.
        // Peak thrust coincides with the server's fast middle dash ticks.
        {f(0f,    0,0,0,0,0,0),
         f(.16f, .08f,-.11f,.18f, 18,-12,7),
         f(.30f, .09f,-.14f,.26f, 24,-13,7),
         f(.44f, .00f,.01f,-.76f, -57,1,0),
         f(.73f, -.02f,-.03f,-.30f, -26,2,2),
         f(1f,   0,0,0,0,0,0)},
        // 8: whip — wind around the shoulder, snap and recoil sideways.
        {f(0f,    0,0,0,0,0,0),
         f(.23f, .25f,.04f,.21f, -20,-65,45),
         f(.42f, .32f,.08f,.24f, -37,-88,62),
         f(.57f, -.26f,-.07f,-.32f, 18,62,-69),
         f(.75f, -.15f,-.05f,-.19f, 12,29,-35),
         f(1f,    0,0,0,0,0,0)},
        // 9: scythe — draw behind, wide crescent reap, long follow-through.
        {f(0f,    0,0,0,0,0,0),
         f(.21f, -.22f,.11f,.16f, -33,56,-31),
         f(.40f, -.30f,.17f,.22f, -51,76,-49),
         f(.62f, .29f,-.16f,-.33f, 27,-64,67),
         f(.82f, .14f,-.13f,-.22f, 18,-29,36),
         f(1f,   0,0,0,0,0,0)}
    };

    private static final float[][] DRAW = {
        f(0f,   0,-.17f,.18f, 34, 0, -14),
        f(.22f, -.13f,-.14f,.13f, 28,-26, -8),
        f(.44f, -.16f,.10f,-.16f, -38,-28, 35),
        f(.67f, .08f,.13f,-.29f, -56,17, -19),
        f(.84f, .04f,.04f,-.09f, -18,8, -8),
        f(1f, 0,0,0, 0,0,0)
    };

    private static final float[][] WINDUP = {
        f(0f, 0,0,0, 0,0,0),
        f(.37f, -.09f,-.11f,.11f, 19,-20,-15),
        f(.73f, -.14f,-.18f,.15f, 30,-28,-23),
        f(1f, -.14f,-.18f,.15f, 30,-28,-23)
    };

    /** V-key only: quiet ready stance, a short acceleration, then a vanishing lunge. */
    private static final float[][] CINEMATIC_OPENING = {
        f(0f, 0, 0, 0, 0, 0, 0),
        f(.17f, .05f, -.11f, .10f, 19, -12, 8),
        f(.46f, .10f, -.16f, .15f, 27, -18, 12),
        f(.64f, .04f, -.10f, -.12f, -21, -8, 6),
        f(.84f, -.08f, -.12f, -.28f, -37, 3, -6),
        f(1f, -.12f, -.10f, -.34f, -41, 6, -9)
    };

    private static final float[][] FINISH = {
        f(0f, -.10f,.10f,.12f, -37,54,-29),
        f(.17f, -.22f,.13f,.20f, -55,80,-48),
        f(.49f, .28f,-.20f,-.35f, 36,-78,82),
        f(.75f, .16f,-.15f,-.23f, 24,-36,40),
        f(1f, 0,0,0,0,0,0)
    };

    public static void strike(PoseStack pose, int form, double progress, boolean leftHand) {
        apply(pose, STRIKES[Math.max(1, Math.min(9, form))], progress, leftHand);
    }

    public static void draw(PoseStack pose, double progress, boolean leftHand) {
        apply(pose, DRAW, progress, leftHand);
    }

    public static void windup(PoseStack pose, double progress, boolean leftHand) {
        apply(pose, WINDUP, progress, leftHand);
    }

    public static void cinematicOpening(PoseStack pose, double progress, boolean leftHand) {
        apply(pose, CINEMATIC_OPENING, progress, leftHand);
    }

    public static void finish(PoseStack pose, double progress, boolean leftHand) {
        apply(pose, FINISH, progress, leftHand);
    }

    // Single scythe arc: anticipation, one committed slash, follow-through,
    // then a stable low grip. There is no second or third return swing.
    private static final float[][] FINAL_SEQUENCE = {
        f(0f,  -.14f,-.23f,.20f,  21, 36,-26),
        f(.22f,-.29f,.01f,.12f, -30, 78,-43),
        f(.55f,-.03f,.26f,.06f, -82, 28, 33),
        f(.78f, .06f,.31f,.06f,-108, -8, 23),
        f(1f,   .12f,-.17f,.20f,  13,-33, 25)
    };

    public static void finalSequence(PoseStack pose, double progress, boolean leftHand) {
        apply(pose, FINAL_SEQUENCE, progress, leftHand);
    }

    private static float[] f(float t, float x, float y, float z, float rx, float ry, float rz) {
        return new float[] {t,x,y,z,rx,ry,rz};
    }

    /** Time-monotonic cubic interpolation, evaluated every rendered frame. */
    private static void apply(PoseStack pose, float[][] frames, double progress, boolean leftHand) {
        float time = Math.max(0, Math.min(1, (float) progress));
        int i = 0;
        while (i < frames.length - 2 && time > frames[i + 1][0]) i++;
        float[] p1 = frames[i];
        float[] p2 = frames[i + 1];
        float[] p0 = frames[Math.max(0, i - 1)];
        float[] p3 = frames[Math.min(frames.length - 1, i + 2)];
        float span = p2[0] - p1[0];
        float t = span < 0.0001f ? 1 : (time - p1[0]) / span;
        float[] poseValues = new float[6];
        for (int c = 1; c <= 6; c++) {
            // Tangents account for uneven keyframe spacing, avoiding abrupt
            // velocity changes when crossing anticipation/contact/recovery.
            float m1 = i == 0 ? 0 : (p2[c] - p0[c]) / Math.max(.0001f, p2[0] - p0[0]);
            float m2 = i + 2 >= frames.length ? 0 : (p3[c] - p1[c]) / Math.max(.0001f, p3[0] - p1[0]);
            float t2 = t*t;
            float t3 = t2*t;
            poseValues[c-1] = (2*t3-3*t2+1)*p1[c] + (t3-2*t2+t)*span*m1
                            + (-2*t3+3*t2)*p2[c] + (t3-t2)*span*m2;
        }
        float mirror = leftHand ? -1f : 1f;
        pose.translate(poseValues[0]*mirror, poseValues[1], poseValues[2]);
        pose.mulPose(Axis.XP.rotationDegrees(poseValues[3]));
        pose.mulPose(Axis.YP.rotationDegrees(poseValues[4]*mirror));
        pose.mulPose(Axis.ZP.rotationDegrees(poseValues[5]*mirror));
    }
}
