// DT_RetryReads.h  Assignment 6, Rex Machina.
// Row struct for the retry read DataTable. One row per phase gate and register.
#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "DT_RetryReads.generated.h"

USTRUCT(BlueprintType)
struct FRetryReadRow : public FTableRowBase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Gate;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   Phase = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString ChargeBand;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Line;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   WordCount = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   Attempts = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString RulesFired;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Provenance;
};
