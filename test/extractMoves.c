#include "global.h"
#include "battle.h"
#include "test/test.h"
#include "global.h"
#include "test/gf_string.h"
#include "constants/battle_move_effects.h"

extern const struct MoveInfo gMovesInfo[];

TEST("Extract Moves")
{
    DebugPrintf("===MOVES DEBUG OUTPUT START===");

    for (u32 i = 0; i < MOVES_COUNT_DYNAMAX; i++)
    {
        // Skip MOVE_NONE (usually index 0)
        if (i == MOVE_NONE)
            continue;

        const struct MoveInfo *move = &gMovesInfo[i];

        // Print basic ability info
        DebugPrintf("- id: %u", i);
        DebugPrintf("  name: %S", move->name);
        if (move->description != NULL)
        {
            char descBuf[256];
            ConvertGfStringToUtf8(move->description, descBuf);
            DebugPrintf("  description: %s", descBuf);
        }
        else
        {
            DebugPrintf("  description: null");
        }

        if(move->effect == EFFECT_RETURN)
        {
            DebugPrintf("  power: %u", 102);
        }
        else if(move->power != 0)
        {
            DebugPrintf("  power: %u", move->power);
        }

        else
        {
            DebugPrintf("  power: %u", 0);
        }
        DebugPrintf(""); // Blank line
    }

    DebugPrintf("===MOVES DEBUG OUTPUT END===");
}