# Developer Templates

This directory contains **work-in-progress templates** for HealthChain developers.

## Purpose

- 🔧 **Development workspace** for new templates
- ⚠️ **Experimental features** not ready for bundling
- 🧪 **Testing ground** before promoting to `healthchain/configs/`

## Workflow

1. **Develop here** - Create/fix templates in subdirectories
2. **Test thoroughly** - Use integration tests and real data
3. **Promote when stable** - Move to `healthchain/configs/` for bundling
4. **Update docs** - Move from "experimental" to "stable" in docs

## Current Templates

None right now — this directory is the staging ground for the next template contribution.

## Guidelines

- Each template type gets its own subdirectory
- Include README with known issues and usage
- Test with example CDAs in `resources/`
- Follow existing template patterns

## Not for End Users

End users should use:
```bash
healthchain init-configs my_configs  # Gets stable bundled templates
```

This directory is for **HealthChain contributors only**.
