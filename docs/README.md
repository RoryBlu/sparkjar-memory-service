# Memory System Documentation

Welcome to the SparkJAR Memory System documentation. This system provides hierarchical, context-aware memory storage for AI agents.

## 📚 Documentation Structure

### Core Documentation
- **[Master Guide](./MEMORY_SYSTEM_MASTER_GUIDE.md)** - Complete overview and quick start
- **[API Reference](./api-reference.md)** - All endpoints with examples
- **[Access Patterns](./access-patterns.md)** - Best practices for crews
- **[Implementation Summary](./implementation-summary.md)** - Current state and validation results
- **[Entity Structure](./entity-structure.md)** - Entity naming and type conventions

### Additional Resources
- **[MEMORY_CONTEXT_ARCHITECTURE.md](../MEMORY_CONTEXT_ARCHITECTURE.md)** - Actor type system details
- **[HIERARCHICAL_MEMORY_GUIDE.md](../HIERARCHICAL_MEMORY_GUIDE.md)** - Hierarchy implementation
- **[HIERARCHICAL_MEMORY_PATTERNS.md](../HIERARCHICAL_MEMORY_PATTERNS.md)** - Usage patterns

## 🚀 Quick Links

### For Crew Developers
Start with the [Access Patterns Guide](./access-patterns.md) to learn how to use memories in your crews.

### For API Users
See the [API Reference](./api-reference.md) for endpoint documentation.

### For System Understanding
Read the [Master Guide](./MEMORY_SYSTEM_MASTER_GUIDE.md) for complete system overview.

## 📊 Current State

- **Status**: Production Ready
- **Performance**: 75-80ms (remote Supabase)
- **Blog Knowledge**: Synth class 24 fully populated
- **Hierarchy**: 4-layer system with client overrides working

## 🔑 Key Entity Names (Synth Class 24)

```
blog_writing_sop_v4      - Main writing procedure
blog_qa_checklist        - Quality assurance
blog_seo_practices       - SEO best practices
blog_content_types       - Content variations
blog_performance_metrics - KPIs and targets
blog_style_guide         - Writing style
blog_post_json_structure - Output structure
```

## 📁 Archive

Historical planning and migration documents are available in [`/docs/archive/memory/`](../archive/memory/) for reference.