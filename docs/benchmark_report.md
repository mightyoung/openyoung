# PEAS Performance Benchmark Report

**Generated**: 2026-03-20 08:49:24

## Summary

- Timestamp: 2026-03-20T08:49:24.888556

## Parser Performance

- **parser_small**: 0.01ms (threshold: 500ms) ✅ PASS
- **parser_medium**: 0.03ms (threshold: 500ms) ✅ PASS
- **parser_large**: 0.19ms (threshold: 500ms) ✅ PASS

## DriftDetector Performance

- **detector_0**: 0.00ms (threshold: 100ms) ✅ PASS
- **detector_10**: 0.01ms (threshold: 100ms) ✅ PASS
- **detector_100**: 0.03ms (threshold: 100ms) ✅ PASS
- **detector_1000**: 0.35ms (threshold: 100ms) ✅ PASS
- **detector_contract**: 0.20ms (threshold: 100ms) ✅ PASS

## ContractBuilder Performance

- **builder_small**: 0.01ms (threshold: 100ms) ✅ PASS
- **builder_medium**: 0.01ms (threshold: 100ms) ✅ PASS
- **builder_large**: 0.00ms (threshold: 100ms) ✅ PASS

## End-to-End Pipeline

- **pipeline_small**: 0.02ms (threshold: 1000ms) ✅ PASS
- **pipeline_medium**: 0.04ms (threshold: 1000ms) ✅ PASS

## Regression Analysis

### ✅ No Regressions Detected