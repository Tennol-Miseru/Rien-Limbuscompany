package io.github.oraclearsenal;

import java.util.UUID;

/** Player-owned progress; swapping, losing or replacing the pager cannot reset the trial. */
public interface PrescriptTrialAccess {
    int oraclearsenal$getPrescriptCount();
    void oraclearsenal$setPrescriptCount(int count);
    int oraclearsenal$getTrialPhase();
    void oraclearsenal$setTrialPhase(int phase);
    int oraclearsenal$getTrialX();
    int oraclearsenal$getTrialY();
    int oraclearsenal$getTrialZ();
    void oraclearsenal$setTrialPosition(int x, int y, int z);
    UUID oraclearsenal$getTrialBossId();
    void oraclearsenal$setTrialBossId(UUID id);
}
