#include "global.h"
#include "test/battle.h"

SINGLE_BATTLE_TEST("Species info data")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { }
    } SCENE {
        DebugPrintf("=== BEGIN BASE STAT DUMP ===");
        for (u32 species = 0; species < NUM_SPECIES; species++) {
            DebugPrintf("[%S]", gSpeciesInfo[species].speciesName);
            DebugPrintf("Attack = %d", gSpeciesInfo[species].baseAttack);
            DebugPrintf("Defense = %d", gSpeciesInfo[species].baseDefense);
            DebugPrintf("SpAttack = %d", gSpeciesInfo[species].baseSpAttack);
            DebugPrintf("SpDefense = %d", gSpeciesInfo[species].baseSpDefense);
            DebugPrintf("Speed = %d", gSpeciesInfo[species].baseSpeed);
            DebugPrintf("Types = [ \"%S\", \"%S\" ]", gTypesInfo[gSpeciesInfo[species].types[0]].name, gTypesInfo[gSpeciesInfo[species].types[1]].name);
            DebugPrintf("abilities = [ ");
            DebugPrintf("   \"%S\"", gAbilitiesInfo[gSpeciesInfo[species].abilities[0]].name);
            DebugPrintf("   \"%S\"", gAbilitiesInfo[gSpeciesInfo[species].abilities[1]].name);
            DebugPrintf("   \"%S\"", gAbilitiesInfo[gSpeciesInfo[species].abilities[2]].name);
            DebugPrintf("]");
            DebugPrintf("");
        }
    }
}
