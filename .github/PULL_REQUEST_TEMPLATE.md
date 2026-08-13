name: Pull request
description: Describe your change
body:
  - type: textarea
    id: summary
    attributes:
      label: Summary
      description: What does this PR change and why?
    validations:
      required: true
  - type: checkboxes
    id: checks
    attributes:
      label: Checklist
      options:
        - label: "Tests pass (pytest)"
        - label: "New code has tests"
        - label: "README / docs updated if needed"
        - label: "License remains Apache-2.0"
    validations:
      required: true
