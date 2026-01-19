# UI Redesign Guide

## Design System

### Spacing Scale
- **Page margins**: 32px
- **Section spacing**: 24px
- **Card padding**: 20-24px
- **Item spacing**: 12-16px
- **Field groups**: 8px between label and input

### Component Sizing
- **Labels**: Auto height, 13px font, 600 weight
- **Inputs/ComboBoxes**: 44px minimum height
- **Buttons**: 44-48px minimum height
- **Date Pickers**: 44px minimum height
- **Tables**: 32px row height minimum

### Typography
```python
# Page Titles
font_size: 22px
font_weight: bold (700)
color: #F5F3FF

# Section Titles (uppercase)
font_size: 11px
font_weight: bold (700)
letter-spacing: 1px
color: #8B5CF6

# Field Labels
font_size: 13px
font_weight: medium (600)
color: #DDD6FE
letter-spacing: 0.3px

# Body Text
font_size: 13-14px
color: #E2E4F0
```

### Layout Patterns

#### Pattern 1: Page with Filters (Earnings, Expenses, Payments)
```
┌─────────────────────────────────────────────────────────┐
│ [Icon] Page Title                                       │
│        Subtitle                                         │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ FILTERS                                             ││
│ │                                                     ││
│ │ View Mode                                           ││
│ │ [Dropdown ▼]                                        ││
│ │                                                     ││
│ │ Date Range                                          ││
│ │ [From Date ▼] [To Date ▼] [Apply Button]          ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ SUMMARY                                             ││
│ │ [Table with data]                                   ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ TRANSACTIONS                                        ││
│ │ [Detailed table]                                    ││
│ └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

#### Pattern 2: Dashboard Cards (Yearly Summary)
```
┌─────────────────────────────────────────────────────────┐
│ [Icon] Page Title        Year: [2024 ▼]                │
│        Subtitle                                         │
│                                                         │
│ ┌──────────────────────┐  ┌──────────────────────────┐│
│ │ TOTAL EARNED         │  │ TOTAL SPENT              ││
│ │ $XX,XXX.XX           │  │ $XX,XXX.XX               ││
│ │                      │  │                          ││
│ │ By Category          │  │ By Category              ││
│ │ [Tree widget]        │  │ [Tree widget]            ││
│ │                      │  │                          ││
│ └──────────────────────┘  └──────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

#### Pattern 3: Form with Actions (Upload, Mapper, Settings)
```
┌─────────────────────────────────────────────────────────┐
│ [Icon] Page Title                                       │
│        Subtitle                                         │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ FORM SECTION                                        ││
│ │                                                     ││
│ │ Field Label                                         ││
│ │ [Input field with 44px height ──────────────────]  ││
│ │                                                     ││
│ │ Another Label                                       ││
│ │ [Dropdown with 44px height ▼]                      ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ [Action Button]  [Secondary]             [Tertiary]    │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ RESULTS / INFO                                      ││
│ │ [Content area]                                      ││
│ └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Implementation Checklist

### For Every Page:

- [ ] Add scroll area for content overflow
- [ ] Use consistent margins (32px)
- [ ] Section spacing (24px between major sections)
- [ ] Card padding (20-24px)

### For Headers:

- [ ] Page title: 22px, bold, #F5F3FF
- [ ] Optional icon (28px emoji)
- [ ] Subtitle: 13px, #A78BFA
- [ ] Right-aligned controls if needed

### For Forms:

- [ ] Labels above inputs (not inline)
- [ ] 8px spacing between label and input
- [ ] All inputs: 44px minimum height
- [ ] Consistent button heights: 44-48px
- [ ] Use ModernPageMixin utilities

### For Tables:

- [ ] Minimum row height: 32px
- [ ] Right-align numeric columns
- [ ] Use alternating row colors
- [ ] Purple-themed selection color

### For Cards:

- [ ] Use create_card() from ModernPageMixin
- [ ] Section titles in uppercase
- [ ] Consistent border radius (18px)
- [ ] Purple gradient background

### For Buttons:

- [ ] Primary: Full purple gradient (default QPushButton)
- [ ] Secondary: Transparent with purple border
- [ ] Minimum height: 44px
- [ ] Minimum width: 100-120px
- [ ] Use create_action_button() when possible

## Color Palette

### Royal Violet Theme (Dark)
```
Backgrounds:
- Window: #0A0E1A → #1A0E2E (gradient)
- Cards: rgba(30, 16, 51, 0.6) → rgba(20, 12, 36, 0.4)
- Inputs: rgba(17, 24, 39, 0.7)

Borders:
- Default: rgba(168, 85, 247, 0.15)
- Hover: rgba(168, 85, 247, 0.3)
- Focus: rgba(168, 85, 247, 0.5)

Text:
- Primary: #F5F3FF
- Secondary: #DDD6FE
- Tertiary: #A78BFA
- Muted: #8B5CF6

Accents:
- Purple: #9333EA, #7C3AED, #8B5CF6
- Success: #10B981
- Error: #EF4444
```

## Common Mistakes to Avoid

1. **❌ Don't**: Place labels inline with inputs
   **✓ Do**: Stack labels above inputs

2. **❌ Don't**: Mix different input heights
   **✓ Do**: Use consistent 44px minimum

3. **❌ Don't**: Cram controls in header row
   **✓ Do**: Create separate filter card

4. **❌ Don't**: Use mixed spacing (8,10,12,16,24)
   **✓ Do**: Stick to scale (12,16,20,24,32)

5. **❌ Don't**: Inline styles for every widget
   **✓ Do**: Use ModernPageMixin utilities

## Example Refactor

### Before:
```python
header_row = QtWidgets.QHBoxLayout()
header_row.addWidget(QtWidgets.QLabel("Title"))
header_row.addWidget(QtWidgets.QLabel("View:"))
header_row.addWidget(self.view_combo)
header_row.addWidget(QtWidgets.QLabel("Month:"))
header_row.addWidget(self.month_combo)
header_row.addWidget(QtWidgets.QLabel("Year:"))
header_row.addWidget(self.year_combo)
header_row.addWidget(self.apply_btn)
```

### After:
```python
# Header
header = ModernPageMixin.create_page_header(
    title="Page Title",
    subtitle="Description",
    icon="📊"
)
layout.addWidget(header)

# Filters Card
filters_card, filters_layout = ModernPageMixin.create_card("FILTERS")

# View Mode
view_label = ModernPageMixin.create_control_label("View Mode")
filters_layout.addWidget(view_label)
self.view_combo = QtWidgets.QComboBox()
ModernPageMixin.style_combo_box(self.view_combo, min_height=44)
filters_layout.addWidget(self.view_combo)

# Date Range (horizontal)
date_container, date_layout = ModernPageMixin.create_controls_row()
# ... add date controls
filters_layout.addWidget(date_container)

layout.addWidget(filters_card)
```

## Testing Checklist

After redesigning each page, verify:

- [ ] No button overlaps at various window sizes
- [ ] All controls are properly aligned
- [ ] Consistent heights across inputs
- [ ] Proper spacing maintained
- [ ] Scroll works when content exceeds viewport
- [ ] Light theme works (if applicable)
- [ ] Hover/focus states work correctly
- [ ] Functionality remains intact
