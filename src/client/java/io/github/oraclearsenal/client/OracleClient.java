package io.github.oraclearsenal.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.particle.v1.ParticleFactoryRegistry;
import io.github.oraclearsenal.RienParticles;
import io.github.oraclearsenal.OracleArsenal;

/** First-person motion is rendered by FirstPersonWeaponMixin on this client. */
public final class OracleClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        // PlayerModel with animated arms, custom skin, and the real held staff item.
        EntityRendererRegistry.register(OracleArsenal.RIEN_NPC, RienNpcRenderer::new);
        ParticleFactoryRegistry.getInstance().register(RienParticles.BLUE_PETAL, BluePetalParticle.Provider::new);
        OraclePlayerAnimations.register();
        RienSkillKeybind.register();
        BlinkAfterimageRenderer.register();
        HermesProgressHud.register();
        // Existing player first-person keyframes remain Mixin-driven.
    }
}
