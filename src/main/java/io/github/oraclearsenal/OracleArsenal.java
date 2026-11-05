package io.github.oraclearsenal;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.sounds.SoundEvents;
import java.util.Map;
import java.util.List;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class OracleArsenal implements ModInitializer {
    public static final String MOD_ID = "oraclearsenal";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    /**
     * Canon weapon after the art pass correction:
     * 神谕终端·双蛇杖 is one transforming weapon, not two separate items.
     */
    public static final Item TWIN_SERPENT_STAFF = Registry.register(BuiltInRegistries.ITEM,
            id("twin_serpent_staff"), new OracleWeaponItem(new Item.Properties()
                    .stacksTo(1).rarity(Rarity.COMMON)));

    /** 1.21.1 armor material format (not the 1.21.2+ equipment asset format). */
    public static final Holder<ArmorMaterial> RIEN_MASK_MATERIAL = Registry.registerForHolder(
            BuiltInRegistries.ARMOR_MATERIAL, id("rien_mask"), new ArmorMaterial(
                    Map.of(ArmorItem.Type.HELMET, 1,
                            ArmorItem.Type.CHESTPLATE, 0,
                            ArmorItem.Type.LEGGINGS, 0,
                            ArmorItem.Type.BOOTS, 0,
                            ArmorItem.Type.BODY, 0),
                    15, SoundEvents.ARMOR_EQUIP_GENERIC,
                    () -> Ingredient.of(Items.QUARTZ),
                    List.of(new ArmorMaterial.Layer(id("rien_mask"))),
                    0.0f, 0.0f));

    public static final Item RIEN_MASK = Registry.register(BuiltInRegistries.ITEM,
            id("rien_mask"), new RienMaskItem(RIEN_MASK_MATERIAL,
                    new Item.Properties().stacksTo(1).durability(ArmorItem.Type.HELMET.getDurability(12))
                            .rarity(Rarity.RARE)));

    public static final Item PRESCRIPT_PAGER = Registry.register(BuiltInRegistries.ITEM,
            id("prescript_pager"), new PrescriptPagerItem(new Item.Properties()
                    .stacksTo(1).rarity(Rarity.RARE)));

    public static final EntityType<RienNpcEntity> RIEN_NPC = Registry.register(
            BuiltInRegistries.ENTITY_TYPE, id("rien"),
            EntityType.Builder.of(RienNpcEntity::new, MobCategory.CREATURE)
                    .sized(.6f, 1.8f).clientTrackingRange(10).build("oraclearsenal:rien"));

    public static final Item RIEN_SPAWN_EGG = Registry.register(BuiltInRegistries.ITEM,
            id("rien_spawn_egg"), new SpawnEggItem(RIEN_NPC, 0x18191C, 0xD5B16E,
                    new Item.Properties()));

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.COMBAT).register(entries -> {
            entries.accept(TWIN_SERPENT_STAFF);
            entries.accept(PRESCRIPT_PAGER);
            entries.accept(RIEN_MASK);
        });
        FabricDefaultAttributeRegistry.register(RIEN_NPC, RienNpcEntity.createAttributes());
        ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.SPAWN_EGGS).register(entries ->
                entries.accept(RIEN_SPAWN_EGG));
        RienSounds.register();
        RienParticles.register();
        RienAfterimages.register();
        // Register Heart before players/NPCs can receive the new status effect.
        HeartEffect.HEART.value();
        OracleCombat.register();
        LOGGER.info("Rien Mod initialized: single caduceus weapon / nine canonical forms + longsword morph / teleport / cinematic chain / prescript pager / Rien half-mask / autonomous player-model Rien NPC.");
    }
}
