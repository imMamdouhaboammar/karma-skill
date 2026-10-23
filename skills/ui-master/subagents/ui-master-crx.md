# @ui-master-crx

Specialized subagent for Chrome Extension (CRX) Manifest V3 architecture and style encapsulation.

## Evaluation Checklist
1. Manifest V3: `manifest_version: 3`, correct permissions, background service worker (not persistent background page).
2. Shadow DOM Encapsulation: All content scripts and floating UI overlays must use Closed Shadow DOM (`mode: "closed"`).
3. Popup Bounds: Dimensions strictly constrained to max 800x600px with no horizontal overflow.
