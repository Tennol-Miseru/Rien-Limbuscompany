package io.github.oraclearsenal;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import java.util.UUID;

/** Autonomous Rien NPC: stronger guardian, one-time half-health mask removal and occasional prescripts. */
public final class RienNpcEntity extends PathfinderMob {
    private static final EntityDataAccessor<Integer> COMBO_STAGE =
            SynchedEntityData.defineId(RienNpcEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> CURRENT_FORM =
            SynchedEntityData.defineId(RienNpcEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> MASK_REMOVED =
            SynchedEntityData.defineId(RienNpcEntity.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> MASK_REMOVAL_TICKS =
            SynchedEntityData.defineId(RienNpcEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> PAGER_READING_TICKS =
            SynchedEntityData.defineId(RienNpcEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> ULTIMATE_WINDUP_TICKS =
            SynchedEntityData.defineId(RienNpcEntity.class, EntityDataSerializers.INT);
    // Player-animator clip currently driving the body, plus the game time it
    // started at. The client evaluates the same keyframe file a player would,
    // so the NPC's swings are the player's swings instead of hand-written poses.
    private static final EntityDataAccessor<String> ANIMATION_CLIP =
            SynchedEntityData.defineId(RienNpcEntity.class, EntityDataSerializers.STRING);
    private static final EntityDataAccessor<Long> ANIMATION_START =
            SynchedEntityData.defineId(RienNpcEntity.class, EntityDataSerializers.LONG);

    private static final int MASK_REMOVAL_DURATION = 28;
    /** Resistance V for exactly the mask-removal (phase change) window. */
    private static final int PHASE_RESISTANCE_AMPLIFIER = 4;
    /** The ninth beat fades in at 0.85 s; keep the finisher pose about a second longer. */
    private static final int FINISHER_HOLD_TICKS = 40;
    private static final int PAGER_READING_DURATION = 36;
    private static final int ULTIMATE_WINDUP_DURATION = 60;
    private static final int ULTIMATE_PRESCRIPT_RECEIVE_REMAINING = 45;
    private static final int ULTIMATE_PRESCRIPT_VARIANTS = 3;
    private static final float OLD_MAX_HEALTH = 120.0f;
    private static final float NEW_MAX_HEALTH = 360.0f;
    // Against a player, Rien spends most of the fight in a readable, punishable
    // neutral round. His previous high-frequency blink AI runs only during a
    // short offensive burst; changing phases never changes his stats or armor.
    private static final int NORMAL_BLINK_MIN_HITS = 3;
    private static final int NORMAL_BLINK_VARIANCE = 3; // 3-5 real, accepted hits
    private static final int NORMAL_BLINK_COOLDOWN = 60; // minimum 3 seconds
    private static final int TARGET_LOST_GRACE = 100;   // temporary LOS loss is fine

    private int nextBlinkTick;
    private int nextAttackTick;
    private int nextUltimateTick;
    private int nextPrescriptTick;
    private UUID playerOpponent;
    private int lastPlayerEngagedTick;
    private boolean offensiveRound;
    private int roundEndTick;
    private int normalHitsTaken;
    private int normalHitsNeeded;
    private int comboStage;
    private int comboNextTick;
    private int comboHoldUntil;
    // Transient NPC Furioso telegraph: 60 ticks before the first blink.
    private int ultimateWindupEndTick;
    private int ultimatePrescriptIndex = -1;
    private boolean ultimatePrescriptReceived;
    private int maskRemovalTicks;
    private int pagerReadingTicks;
    private int prescriptIndex = -1;
    private UUID trialOwner;
    private boolean trialDefeated;
    private int trialSecondPhaseTicks;
    private int trialDefeatTicks;

    public void assignTrialOwner(ServerPlayer owner) {
        this.trialOwner = owner.getUUID();
        this.setTarget(owner);
        this.setPersistenceRequired();
        this.setDropChance(EquipmentSlot.MAINHAND, 0.0f);
    }

    private boolean isTrialTarget(LivingEntity target) {
        return trialOwner == null || (target instanceof ServerPlayer player
                && player.getUUID().equals(trialOwner));
    }

    private void finishTrial(ServerLevel level) {
        if (trialDefeated || trialOwner == null) return;
        trialDefeated = true;
        trialDefeatTicks = 200;
        endCombo();
        this.getNavigation().stop();
        this.setTarget(null);
        this.setNoAi(true);
        this.setInvulnerable(true);
        this.setHealth(Math.max(1f, getMaxHealth() * .10f));
        ServerPlayer owner = level.getServer().getPlayerList().getPlayer(trialOwner);
        if (owner != null) PrescriptTrial.completed(owner, this);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 1.3, getZ(),
                40, .45, .7, .45, .05);
    }


    public RienNpcEntity(EntityType<? extends PathfinderMob> type, Level level) {
        super(type, level);
        this.xpReward = 18;
        this.setPersistenceRequired();
        this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(OracleArsenal.TWIN_SERPENT_STAFF));
        // The porcelain mask is painted into the phase-one skin. Do not equip
        // a second 3D helmet over Rien's face: it obscures his facial design.
        this.setItemSlot(EquipmentSlot.HEAD, ItemStack.EMPTY);
        this.setDropChance(EquipmentSlot.HEAD, 0.0f);
        this.setDropChance(EquipmentSlot.OFFHAND, 0.0f);
        // Attribute registration has already happened by the time the mob is constructed.
        this.setHealth(this.getMaxHealth());
        this.nextBlinkTick = 30;
        this.nextUltimateTick = 70;
        this.nextPrescriptTick = 500 + this.random.nextInt(500);
        this.normalHitsNeeded = rollNormalHitThreshold();
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, NEW_MAX_HEALTH)
                .add(Attributes.MOVEMENT_SPEED, 0.34)
                .add(Attributes.ATTACK_DAMAGE, 11)
                .add(Attributes.ARMOR, 15)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.75)
                .add(Attributes.FOLLOW_RANGE, 32);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(COMBO_STAGE, 0);
        builder.define(CURRENT_FORM, 1);
        builder.define(MASK_REMOVED, false);
        builder.define(MASK_REMOVAL_TICKS, 0);
        builder.define(PAGER_READING_TICKS, 0);
        builder.define(ULTIMATE_WINDUP_TICKS, 0);
        builder.define(ANIMATION_CLIP, "");
        builder.define(ANIMATION_START, 0L);
    }

    public int getComboStage() { return this.entityData.get(COMBO_STAGE); }
    public int getCurrentForm() { return this.entityData.get(CURRENT_FORM); }
    public boolean hasRemovedMask() { return this.entityData.get(MASK_REMOVED); }
    public int getMaskRemovalTicks() { return this.entityData.get(MASK_REMOVAL_TICKS); }
    public int getPagerReadingTicks() { return this.entityData.get(PAGER_READING_TICKS); }
    public int getUltimateWindupTicks() { return this.entityData.get(ULTIMATE_WINDUP_TICKS); }
    public String getAnimationClip() { return this.entityData.get(ANIMATION_CLIP); }
    public long getAnimationStart() { return this.entityData.get(ANIMATION_START); }

    /** Starts one of the shared player animations on this NPC. */
    private void playAnimation(String clip) {
        this.entityData.set(ANIMATION_CLIP, clip);
        this.entityData.set(ANIMATION_START, this.level().getGameTime());
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        // The vanilla melee goal has its own cooldown independent of the
        // attack-speed attribute. Apply the Heart interval there as well,
        // otherwise Rien would not actually attack faster during the buff.
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, true) {
            @Override
            protected int getAttackInterval() {
                return RienNpcEntity.this.hasEffect(HeartEffect.HEART)
                        ? 17 : super.getAttackInterval();
            }
        });
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.85));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Monster.class,
                10, true, false, entity -> !(entity instanceof RienNpcEntity)));
    }

    /**
     * Player-only twin-serpent-staff protection never belongs to the NPC.
     * Reject Resistance from any effect source, including external effects,
     * so an autonomous Furioso or blink cannot turn the trial boss invulnerable.
     * Other potion effects and the NPC's intended armor remain unchanged.
     */
    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        // The only Resistance Rien may ever hold is the short phase-change ward
        // granted by beginMaskRemoval(). All external Resistance is still refused.
        if (effect.getEffect().equals(MobEffects.DAMAGE_RESISTANCE)) {
            return maskRemovalTicks > 0;
        }
        return super.canBeAffected(effect);
    }

    @Override
    public boolean removeWhenFarAway(double distanceToClosestPlayer) { return false; }

    @Override
    public boolean doHurtTarget(net.minecraft.world.entity.Entity entity) {
        if (!(entity instanceof LivingEntity target) || !isValidTarget(target) || comboStage != 0
                || maskRemovalTicks > 0 || pagerReadingTicks > 0
                || ultimateWindupEndTick > 0
                || this.tickCount < nextAttackTick || distanceToSqr(target) > 4.8 * 4.8) return false;
        // In the long normal round the weapon remains readable. Only a
        // successful, hit-earned blink morphs it; the offensive round retains
        // the old fast changing forms on every strike.
        int form = target instanceof Player && !offensiveRound
                ? getCurrentForm() : this.random.nextInt(9) + 1;
        if (!(target instanceof Player) || offensiveRound) morph(form);
        boolean hit = OracleCombat.applyStage(this, target, form, false);
        // Ordinary swings use the same weapon clip a player would play.
        playAnimation(form >= 9 ? "furioso_final_pose" : "attack_form_" + form);
        int attackDelay = hasRemovedMask() ? 10 + this.random.nextInt(6)
                : 14 + this.random.nextInt(7);
        if (hasEffect(HeartEffect.HEART)) {
            attackDelay = Math.max(1, (int) Math.ceil(attackDelay / 1.15));
        }
        nextAttackTick = this.tickCount + attackDelay;
        return hit;
    }

    // This must live in tick(), not customServerAiStep(): no-AI entities skip AI ticks.
    @Override
    public void tick() {
        super.tick();
        // Compatibility with old saves: strip the obsolete visual helmet.
        // The masked/unmasked entity skin and half-health gesture still decide
        // when Rien reveals his scarred face.
        if (!level().isClientSide && getItemBySlot(EquipmentSlot.HEAD).is(OracleArsenal.RIEN_MASK)) {
            setItemSlot(EquipmentSlot.HEAD, ItemStack.EMPTY);
        }
        // Clear Resistance from existing saves or forced effect insertion too.
        // Player protection stays intact; this only runs on RienNpcEntity.
        // During the phase change the ward is intentional and stays up.
        if (!level().isClientSide && maskRemovalTicks == 0
                && hasEffect(MobEffects.DAMAGE_RESISTANCE)) {
            removeEffect(MobEffects.DAMAGE_RESISTANCE);
        }
        if (trialDefeated && !level().isClientSide && --trialDefeatTicks <= 0) discard();
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        if (!(this.level() instanceof ServerLevel level)) return;
        if (trialDefeated) return;
        if (trialOwner != null) {
            ServerPlayer challenger = level.getServer().getPlayerList().getPlayer(trialOwner);
            if (challenger != null && challenger.level() == level && challenger.isAlive()
                    && distanceToSqr(challenger) < 48 * 48) setTarget(challenger);
            else setTarget(null);
            if (hasRemovedMask() && maskRemovalTicks == 0) trialSecondPhaseTicks++;
        }
        if (!hasRemovedMask() && isAlive() && getHealth() <= getMaxHealth() * 0.5f) {
            beginMaskRemoval(level);
        }
        if (maskRemovalTicks > 0) {
            tickMaskRemoval(level);
            return;
        }
        if (pagerReadingTicks > 0) {
            tickPager(level);
            return;
        }
        LivingEntity target = getTarget();
        boolean valid = isValidTarget(target);
        // A combat round is used only against players. Against mobs Rien keeps
        // his old autonomous blink and multi-weapon attack scheduling.
        boolean playerFight = valid && target instanceof Player;
        if (playerFight && getSensing().hasLineOfSight(target)
                && distanceToSqr(target) <= 20 * 20) {
            maintainPlayerRound((Player) target, level);
        } else if (playerOpponent != null) {
            if (tickCount - lastPlayerEngagedTick > TARGET_LOST_GRACE) {
                resetPlayerRound();
            } else {
                // Hiding behind cover briefly should not consume the player's
                // ordinary-round opportunity or force an offensive burst on return.
                roundEndTick++;
            }
        }
        if (ultimateWindupEndTick > 0) {
            // An invalid target or an interrupted phase cancels the queued
            // strike instead of letting a delayed teleport occur out of combat.
            if (!valid || !getSensing().hasLineOfSight(target)
                    || distanceToSqr(target) > 14 * 14
                    || maskRemovalTicks > 0 || pagerReadingTicks > 0
                    || (playerFight && !offensiveRound)) {
                clearUltimateWindup();
                nextUltimateTick = Math.max(nextUltimateTick, tickCount + 30);
                return;
            }
            getNavigation().stop();
            int remaining = Math.max(0, ultimateWindupEndTick - tickCount);
            entityData.set(ULTIMATE_WINDUP_TICKS, remaining);
            if (remaining > 0) {
                if (!ultimatePrescriptReceived && remaining <= ULTIMATE_PRESCRIPT_RECEIVE_REMAINING) {
                    receiveUltimatePrescript(level);
                }
                RienDarkAura.npcWindup(level, this, remaining);
                return;
            }
            clearUltimateWindup();
            if (startNineBeatCombo(level, target)) return;
            nextUltimateTick = tickCount + 35;
            return;
        }
        if (comboStage > 0) {
            if (this.tickCount >= comboNextTick) {
                if (comboStage > 9) {
                    // Hold the finisher pose before returning to neutral.
                    if (this.tickCount < comboHoldUntil) {
                        getNavigation().stop();
                        return;
                    }
                    endCombo();
                } else {
                    int stage = comboStage;
                    if (valid && (distanceToSqr(target) > 4.5 * 4.5 || stage == 4 || stage == 7)) {
                        blinkNear(target);
                    }
                    morph(stage);
                    if (valid && distanceToSqr(target) < 5.0 * 5.0 && getSensing().hasLineOfSight(target)) {
                        OracleCombat.applyStage(this, target, stage, true);
                    } else {
                        Vec3 whiff = getEyePosition().add(getLookAngle().scale(2));
                        level.sendParticles(stage == 9 ? ParticleTypes.END_ROD : ParticleTypes.CRIT,
                                whiff.x, whiff.y, whiff.z, 12, .45, .4, .45, .12);
                        swing(InteractionHand.MAIN_HAND, true);
                        RienSounds.playAttack(level, blockPosition(), SoundSource.HOSTILE, stage, .48f);
                    }
                    this.entityData.set(COMBO_STAGE, stage);
                    playAnimation(stage >= 9 ? "furioso_final_pose" : "attack_form_" + stage);
                    if (stage >= 9) comboHoldUntil = this.tickCount + FINISHER_HOLD_TICKS;
                    comboStage++;
                    comboNextTick = this.tickCount + (hasRemovedMask() ? 4 : 5);
                }
            }
            return;
        }

        // Low-frequency idle action; defer it if an enemy is threatening Rien at close range.
        if (tickCount >= nextPrescriptTick) {
            if (!valid || distanceToSqr(target) > 10 * 10) {
                beginPager(level);
                return;
            }
            nextPrescriptTick = tickCount + 80;
        }
        if (!valid || !getSensing().hasLineOfSight(target) || distanceToSqr(target) > 20 * 20) return;

        // Ordinary rounds never initiate the nine-beat combo. During a burst
        // the exact previous combo cadence and stage-by-stage blinks remain.
        if ((!playerFight || offensiveRound)
                && tickCount >= nextUltimateTick && distanceToSqr(target) < 14 * 14) {
            // Telegraph for exactly three seconds before any combo blink or hit.
            // Rien raises a pager to receive one of three exclusive Furioso prescripts.
            beginUltimateWindup();
            nextAttackTick = Math.max(nextAttackTick, ultimateWindupEndTick);
            // A player-only offensive burst must last long enough to contain
            // the complete telegraph AND subsequent nine-beat sequence.
            if (playerFight) roundEndTick = Math.max(roundEndTick,
                    ultimateWindupEndTick + (hasRemovedMask() ? 9 * 4 : 9 * 5) + 8);
            level.playSound(null, blockPosition(), RienSounds.RIEN_EFFORT,
                    SoundSource.HOSTILE, .88f, .72f);
            RienDarkAura.npcWindup(level, this, ULTIMATE_WINDUP_DURATION);
            getNavigation().stop();
            return;
        }

        if (tickCount >= nextBlinkTick && distanceToSqr(target) < 17 * 17) {
            // During ordinary combat, time passing alone does NOT grant a blink.
            if (!playerFight || offensiveRound || normalHitsTaken >= normalHitsNeeded) {
                boolean escaped = blinkNear(target);
                if (escaped) {
                    morphDifferentForm();
                    if (playerFight && !offensiveRound) {
                        normalHitsTaken = 0;
                        normalHitsNeeded = rollNormalHitThreshold();
                    }
                }
                if (playerFight && !offensiveRound) {
                    // Failed relocation keeps the earned hit counter and retries
                    // shortly, but never spams teleports every tick.
                    nextBlinkTick = tickCount + (escaped ? NORMAL_BLINK_COOLDOWN : 12);
                } else {
                    // Identical to the previous frequent blink behavior.
                    nextBlinkTick = tickCount + (hasRemovedMask() ? 32 : 48) + random.nextInt(30);
                }
            }
        }
    }

    /** Prepare a unique prescript without changing the ordinary pager's random pool. */
    private void beginUltimateWindup() {
        ultimateWindupEndTick = tickCount + ULTIMATE_WINDUP_DURATION;
        ultimatePrescriptIndex = random.nextInt(ULTIMATE_PRESCRIPT_VARIANTS);
        ultimatePrescriptReceived = false;
        entityData.set(ULTIMATE_WINDUP_TICKS, ULTIMATE_WINDUP_DURATION);
        setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(OracleArsenal.PRESCRIPT_PAGER));
        getNavigation().stop();
    }

    /** The pager beep and the received text happen once after Rien raises his hand. */
    private void receiveUltimatePrescript(ServerLevel level) {
        ultimatePrescriptReceived = true;
        level.playSound(null, blockPosition(), RienSounds.PRESCRIPT_BEEP,
                SoundSource.HOSTILE, .62f, 1f);
        level.sendParticles(ParticleTypes.ENCHANT,
                getX(), getY() + 1.55, getZ(), 10, .25, .18, .25, .018);
        Component message = Component.translatable("message.oraclearsenal.rien_received",
                Component.translatable("message.oraclearsenal.rien_ultimate_prescript."
                        + ultimatePrescriptIndex));
        for (ServerPlayer viewer : level.getPlayers(player -> player.distanceToSqr(this) <= 18 * 18)) {
            viewer.sendSystemMessage(message);
        }
    }

    /** Cancel or finish a telegraph without leaving a pager equipped. */
    private void clearUltimateWindup() {
        boolean wasActive = ultimateWindupEndTick > 0;
        ultimateWindupEndTick = 0;
        ultimatePrescriptIndex = -1;
        ultimatePrescriptReceived = false;
        entityData.set(ULTIMATE_WINDUP_TICKS, 0);
        if (wasActive && getMainHandItem().is(OracleArsenal.PRESCRIPT_PAGER)
                && pagerReadingTicks == 0) {
            restoreStaff();
        }
    }

    /** Invoked only after a complete, uninterrupted 60-tick dark-smoke windup. */
    private boolean startNineBeatCombo(ServerLevel level, LivingEntity target) {
        if (!blinkNear(target)) return false;
        comboStage = 1;
        comboHoldUntil = 0;
        HeartEffect.grant(this);
        comboNextTick = tickCount + 4;
        entityData.set(COMBO_STAGE, 1);
        morph(1);
        nextUltimateTick = tickCount + (hasRemovedMask() ? 150 : 220) + random.nextInt(70);
        nextBlinkTick = tickCount + 55;
        nextAttackTick = tickCount + 48;
        level.playSound(null, blockPosition(), RienSounds.RIEN_EFFORT,
                SoundSource.HOSTILE, .65f, 1f);
        return true;
    }

    private int rollNormalHitThreshold() {
        return NORMAL_BLINK_MIN_HITS + random.nextInt(NORMAL_BLINK_VARIANCE);
    }

    private void morphDifferentForm() {
        int current = getCurrentForm();
        int next = 1 + random.nextInt(8);
        if (next >= current) next++; // uniformly pick a different form from 1-9
        morph(next);
    }

    private void resetPlayerRound() {
        clearUltimateWindup();
        playerOpponent = null;
        offensiveRound = false;
        roundEndTick = 0;
        normalHitsTaken = 0;
        normalHitsNeeded = rollNormalHitThreshold();
    }

    private void enterNormalRound() {
        offensiveRound = false;
        normalHitsTaken = 0;
        normalHitsNeeded = rollNormalHitThreshold();
        // 12-16 seconds (masked) or 10-13 seconds (unmasked). Over 70%
        // of active combat is intended to be ordinary, punishable combat.
        roundEndTick = tickCount + (hasRemovedMask() ? 200 : 240) + random.nextInt(61);
        nextBlinkTick = Math.max(nextBlinkTick, tickCount + NORMAL_BLINK_COOLDOWN);
    }

    private void enterOffensiveRound(ServerLevel level) {
        offensiveRound = true;
        // Brief 4-5 second offensive burst, retaining prior blink frequency.
        roundEndTick = tickCount + (hasRemovedMask() ? 80 : 75) + random.nextInt(21);
        nextBlinkTick = tickCount + 4;
        nextUltimateTick = Math.max(nextUltimateTick, tickCount + 20);
        level.playSound(null, blockPosition(), RienSounds.RIEN_EFFORT,
                SoundSource.HOSTILE, .7f, .85f);
        level.sendParticles(ParticleTypes.CRIT, getX(), getY() + 1.2, getZ(),
                22, .38, .6, .38, .06);
    }

    private void maintainPlayerRound(Player player, ServerLevel level) {
        if (playerOpponent == null || !playerOpponent.equals(player.getUUID())) {
            playerOpponent = player.getUUID();
            enterNormalRound();
        }
        lastPlayerEngagedTick = tickCount;
        // The ninth combo is allowed to finish before the state changes.
        if (tickCount >= roundEndTick && comboStage == 0 && ultimateWindupEndTick == 0) {
            if (offensiveRound) enterNormalRound();
            else enterOffensiveRound(level);
        }
    }

    /** Visually take off the mask once, when HP first falls to half. */
    private void beginMaskRemoval(ServerLevel level) {
        if (hasRemovedMask()) return;
        endCombo();
        // Phase two changes movement speed but still begins with a long
        // ordinary round, not a chain of unavoidable immediate blinks.
        if (playerOpponent != null) enterNormalRound();
        if (pagerReadingTicks > 0) {
            pagerReadingTicks = 0;
            entityData.set(PAGER_READING_TICKS, 0);
            restoreStaff();
        }
        entityData.set(MASK_REMOVED, true);
        maskRemovalTicks = MASK_REMOVAL_DURATION;
        entityData.set(MASK_REMOVAL_TICKS, maskRemovalTicks);
        // Damage immunity for the whole reveal: Resistance V (100% reduction)
        // covering exactly this transition, then stripped again in tick().
        this.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE,
                MASK_REMOVAL_DURATION + 5, PHASE_RESISTANCE_AMPLIFIER,
                false, false, false));
        // The mask is a painted part of the first-phase skin; at midpoint,
        // reveal the second skin and briefly display a removed mask in hand.
        this.getNavigation().stop();
        this.nextAttackTick = tickCount + MASK_REMOVAL_DURATION + 4;
        this.nextUltimateTick = Math.max(nextUltimateTick, tickCount + MASK_REMOVAL_DURATION + 12);
        if (this.getAttribute(Attributes.MOVEMENT_SPEED) != null) {
            this.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(0.39);
        }
        level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 1.6, getZ(), 38, .4, .4, .4, .05);
        level.playSound(null, blockPosition(), RienSounds.MASK_SCARS,
                SoundSource.HOSTILE, .9f, 1f);
    }

    /** Skin-mask reveal synchronized to the face-reaching gesture. */
    private void tickMaskRemoval(ServerLevel level) {
        getNavigation().stop();
        maskRemovalTicks--;
        entityData.set(MASK_REMOVAL_TICKS, maskRemovalTicks);
        if (maskRemovalTicks == MASK_REMOVAL_DURATION / 2) {
            // Gesture prop, not worn armor. It is dropped only once at the end.
            if (!getOffhandItem().is(OracleArsenal.RIEN_MASK)) {
                this.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(OracleArsenal.RIEN_MASK));
            }
        }
        if (maskRemovalTicks == 0) {
            // Drop the exact equipment that was removed, never create another mask.
            ItemStack held = this.getItemBySlot(EquipmentSlot.OFFHAND);
            if (held.is(OracleArsenal.RIEN_MASK)) {
                this.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
                this.spawnAtLocation(held.copy());
            }
            level.playSound(null, blockPosition(), RienSounds.MASK_DROP, SoundSource.HOSTILE, .88f, 1f);
            if (random.nextBoolean()) {
                level.playSound(null, blockPosition(), RienSounds.RIEN_LAUGH, SoundSource.HOSTILE, .65f, 1f);
            }
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY()+1.3, getZ(),
                    30, .3, .55, .3, .08);
        }
    }

    private void beginPager(ServerLevel level) {
        prescriptIndex = random.nextInt(PrescriptPagerItem.PRESCRIPT_COUNT);
        pagerReadingTicks = PAGER_READING_DURATION;
        entityData.set(PAGER_READING_TICKS, pagerReadingTicks);
        this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(OracleArsenal.PRESCRIPT_PAGER));
        this.getNavigation().stop();
        nextPrescriptTick = tickCount + 750 + random.nextInt(600);
        level.playSound(null, blockPosition(), RienSounds.PRESCRIPT_BEEP,
                SoundSource.HOSTILE, .28f, 1f);
    }

    private void tickPager(ServerLevel level) {
        getNavigation().stop();
        pagerReadingTicks--;
        entityData.set(PAGER_READING_TICKS, pagerReadingTicks);
        if (pagerReadingTicks == 10) {
            level.playSound(null, blockPosition(), RienSounds.PRESCRIPT_BEEP,
                    SoundSource.HOSTILE, .28f, 1f);
            level.sendParticles(ParticleTypes.ENCHANT, getX(), getY()+1.55, getZ(), 12, .25, .2, .25, .02);
            for (ServerPlayer viewer : level.getPlayers(p -> p.distanceToSqr(this) <= 18 * 18)) {
                viewer.sendSystemMessage(Component.translatable("message.oraclearsenal.rien_received",
                        Component.translatable("message.oraclearsenal.prescript." + prescriptIndex)));
            }
        }
        if (pagerReadingTicks == 0) restoreStaff();
    }

    private void restoreStaff() {
        ItemStack staff = new ItemStack(OracleArsenal.TWIN_SERPENT_STAFF);
        OracleWeaponItem.setForm(staff, getCurrentForm());
        setItemSlot(EquipmentSlot.MAINHAND, staff);
    }

    private boolean isValidTarget(LivingEntity target) {
        if (target == null || !target.isAlive() || target == this || target instanceof RienNpcEntity
                || !isTrialTarget(target)) return false;
        if (target instanceof Player player && (player.isCreative() || player.isSpectator())) return false;
        return true;
    }

    private void morph(int form) {
        entityData.set(CURRENT_FORM, form);
        ItemStack staff = getMainHandItem();
        boolean changed = staff.getItem() != OracleArsenal.TWIN_SERPENT_STAFF
                || OracleWeaponItem.getForm(staff) != form;
        if (staff.getItem() != OracleArsenal.TWIN_SERPENT_STAFF) {
            staff = new ItemStack(OracleArsenal.TWIN_SERPENT_STAFF);
            setItemSlot(EquipmentSlot.MAINHAND, staff);
        }
        OracleWeaponItem.setForm(staff, form);
        // No duplicate morph cue if the ultimate opening already set form 1.
        if (changed && level() instanceof ServerLevel level) {
            RienSounds.playChange(level, blockPosition(), SoundSource.HOSTILE);
        }
    }

    private void endCombo() {
        clearUltimateWindup();
        comboStage = 0;
        comboHoldUntil = 0;
        entityData.set(COMBO_STAGE, 0);
        playAnimation("");
    }

    private boolean blinkNear(LivingEntity target) {
        if (!(level() instanceof ServerLevel level)) return false;
        double radius = (getBbWidth() + target.getBbWidth()) * .5 + .65;
        double offset = random.nextDouble() * Math.PI * 2;
        for (int dy : new int[]{0, 1, -1, 2, -2}) {
            for (int i = 0; i < 12; i++) {
                double a = offset + i * Math.PI / 6;
                Vec3 dst = new Vec3(target.getX() + Math.cos(a) * radius,
                        target.getY() + dy, target.getZ() + Math.sin(a) * radius);
                BlockPos feet = BlockPos.containing(dst);
                BlockPos below = feet.below();
                if (!level.getWorldBorder().isWithinBounds(feet)
                        || !level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)
                        || !level.getFluidState(feet).isEmpty()
                        || !level.getFluidState(feet.above()).isEmpty()) continue;
                AABB relocated = getBoundingBox().move(dst.subtract(position()));
                if (!level.noCollision(this, relocated)) continue;
                Vec3 origin = position();
                // Freeze the weapon pose for the NEXT NPC strike during a
                // Furioso combo (the morph happens just after this blink).
                RienAfterimages.departure(level, this, origin,
                        comboStage > 0 ? Math.min(9, comboStage) : getCurrentForm(),
                        comboStage > 0 ? 1 : 0);
                RienParticles.departure(level, origin);
                getNavigation().stop();
                teleportTo(dst.x, dst.y, dst.z);
                getLookControl().setLookAt(target, 180, 180);
                this.fallDistance = 0;
                RienParticles.arrival(level, dst);
                return true;
            }
        }
        return false;
    }

    @Override
    public boolean hurt(DamageSource source, float damage) {
        if (trialOwner != null) {
            if (trialDefeated || !(source.getEntity() instanceof ServerPlayer attacker)
                    || !attacker.getUUID().equals(trialOwner)) return false;
            // Nonlethal challenge: the second phase must actually be survived.
            // A fresh hit after the mask-removal animation and 60 combat ticks
            // completes the trial once HP is driven below 12 percent.
            if (hasRemovedMask() && maskRemovalTicks == 0 && trialSecondPhaseTicks >= 60
                    && getHealth() - damage <= getMaxHealth() * .12f
                    && level() instanceof ServerLevel level) {
                finishTrial(level);
                return true;
            }
            damage = Math.min(damage, Math.max(0f, getHealth() - 1f));
            if (damage <= 0) return false;
        }
        float healthBeforeHit = getHealth();
        boolean applied = super.hurt(source, damage);
        if (applied) {
            if (!isAlive()) endCombo();
            else if (level() instanceof ServerLevel level && !hasRemovedMask()
                    && getHealth() <= getMaxHealth() * .5f) beginMaskRemoval(level);
            // Count accepted damage from the current player (including player-
            // owned projectiles), not every hit attempt or invulnerability tick.
            // A mask transition does not earn an immediate blink.
            if (isAlive() && getHealth() < healthBeforeHit && !trialDefeated
                    && maskRemovalTicks == 0 && source.getEntity() instanceof Player attacker
                    && isTrialTarget(attacker)
                    && !offensiveRound && (playerOpponent == null
                    || playerOpponent.equals(attacker.getUUID()))) {
                if (playerOpponent == null) {
                    playerOpponent = attacker.getUUID();
                    enterNormalRound();
                }
                normalHitsTaken = Math.min(normalHitsNeeded, normalHitsTaken + 1);
            }
        }
        return applied;
    }

    @Override
    protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean causedByPlayer) {
        // Take ownership of the item before vanilla equipment-drop processing.
        // Neither slot can then produce a second copy through normal death drops.
        ItemStack worn = this.getItemBySlot(EquipmentSlot.HEAD);
        ItemStack held = this.getItemBySlot(EquipmentSlot.OFFHAND);
        ItemStack mask = worn.is(OracleArsenal.RIEN_MASK) ? worn.copy()
                : held.is(OracleArsenal.RIEN_MASK) ? held.copy() : ItemStack.EMPTY;
        if (worn.is(OracleArsenal.RIEN_MASK)) {
            this.setItemSlot(EquipmentSlot.HEAD, ItemStack.EMPTY);
        }
        if (held.is(OracleArsenal.RIEN_MASK)) {
            this.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
        }
        super.dropCustomDeathLoot(level, source, causedByPlayer);
        if (!mask.isEmpty()) this.spawnAtLocation(mask);
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putBoolean("RienMaskRemoved", hasRemovedMask());
        tag.putInt("RienMaskRemovalTicks", maskRemovalTicks);
        tag.putBoolean("RienBalanceV085", true);
        if (trialOwner != null) tag.putUUID("RienTrialOwner", trialOwner);
        tag.putBoolean("RienTrialDefeated", trialDefeated);
        tag.putInt("RienTrialPhase2Ticks", trialSecondPhaseTicks);
        tag.putInt("RienTrialDefeatTicks", trialDefeatTicks);
        // Combat rounds are intentionally transient: reloading must never
        // resurrect a partial combo of teleports or a stale attack cooldown.
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        // Upgrade old world entities immediately, not after their first AI tick.
        if (!level().isClientSide && hasEffect(MobEffects.DAMAGE_RESISTANCE)) {
            removeEffect(MobEffects.DAMAGE_RESISTANCE);
        }
        trialOwner = tag.hasUUID("RienTrialOwner") ? tag.getUUID("RienTrialOwner") : null;
        trialDefeated = tag.getBoolean("RienTrialDefeated");
        trialSecondPhaseTicks = Math.max(0, tag.getInt("RienTrialPhase2Ticks"));
        trialDefeatTicks = Math.max(1, tag.getInt("RienTrialDefeatTicks"));
        resetPlayerRound();
        comboStage = 0;
        entityData.set(COMBO_STAGE, 0);
        if (trialOwner != null) this.setDropChance(EquipmentSlot.MAINHAND, 0.0f);
        if (trialDefeated) { this.setNoAi(true); this.setInvulnerable(true); }
        // Migrate existing v0.8.4 entities without a sudden drop in relative health.
        if (!tag.getBoolean("RienBalanceV085") && getHealth() > 0) {
            float ratio = Math.min(1f, getHealth() / OLD_MAX_HEALTH);
            setHealth(Math.min(getMaxHealth(), NEW_MAX_HEALTH * ratio));
        }
        boolean removed = tag.getBoolean("RienMaskRemoved") || getHealth() <= getMaxHealth() * .5f;
        entityData.set(MASK_REMOVED, removed);
        if (removed && this.getAttribute(Attributes.MOVEMENT_SPEED) != null) {
            this.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(.39);
        }
        // Resume an interrupted half-health removal, including which actual
        // equipment slot owned the mask. Previous-version NBT has no tick field.
        maskRemovalTicks = removed ? Math.max(0,
                Math.min(MASK_REMOVAL_DURATION, tag.getInt("RienMaskRemovalTicks"))) : 0;
        if (maskRemovalTicks > 0) {
            // Continue the phase-change ward if the world was saved mid-reveal.
            this.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE,
                    maskRemovalTicks + 5, PHASE_RESISTANCE_AMPLIFIER,
                    false, false, false));
        }
        pagerReadingTicks = 0;
        entityData.set(MASK_REMOVAL_TICKS, maskRemovalTicks);
        entityData.set(PAGER_READING_TICKS, 0);
        this.setDropChance(EquipmentSlot.HEAD, 0.0f);
        this.setDropChance(EquipmentSlot.OFFHAND, 0.0f);
        // Migrate old helmet-equipped NPCs: never restore visible head armor.
        if (getItemBySlot(EquipmentSlot.HEAD).is(OracleArsenal.RIEN_MASK)) {
            this.setItemSlot(EquipmentSlot.HEAD, ItemStack.EMPTY);
        }
        // Preserve half-health reveal when loading a world mid-gesture.
        if (maskRemovalTicks > 0 && maskRemovalTicks <= MASK_REMOVAL_DURATION / 2) {
            if (!getOffhandItem().is(OracleArsenal.RIEN_MASK)) {
                this.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(OracleArsenal.RIEN_MASK));
            }
        } else if (getOffhandItem().is(OracleArsenal.RIEN_MASK)) {
            this.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
        }
        if (getMainHandItem().is(OracleArsenal.PRESCRIPT_PAGER)) restoreStaff();
    }
}
