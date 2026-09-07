// DT_JourneyBeats.h  Assignment 7, Rex Machina.
// Row struct for Chronicler journey narration after the Copy Desk pass.
#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "DT_JourneyBeats.generated.h"

USTRUCT(BlueprintType)
struct FJourneyBeatRow : public FTableRowBase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Beat;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString ViolationClass;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   WordBudget = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString ToneTarget;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Narration;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   WordCount = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float   ScoreBefore = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float   ScoreAfter = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   Repairs = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Outcome;
};
