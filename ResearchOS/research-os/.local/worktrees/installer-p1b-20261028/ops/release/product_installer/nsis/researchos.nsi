Unicode true
RequestExecutionLevel user
SetCompressor /FINAL zlib
SetCompress off
Name "ResearchOS ${EDITION}"
OutFile "${OUTFILE}"
InstallDir "$LOCALAPPDATA\Programs\ResearchOS"
Icon "${ICON}"
ShowInstDetails show
AutoCloseWindow false

; P1b is a reviewable carrier, not a transaction executor. The entry guard
; exits before any program, business data, registry, shortcut or PATH write.
Function .onInit
  IfFileExists "$LOCALAPPDATA\Programs\ResearchOS" maintenance
  IfFileExists "$LOCALAPPDATA\ResearchOS" maintenance
  IfFileExists "$LOCALAPPDATA\ResearchOS-Install" maintenance
  MessageBox MB_ICONSTOP "ResearchOS first installation requires the transaction and maintenance component. This media has not installed anything."
  SetErrorLevel 43
  Quit
maintenance:
  MessageBox MB_ICONSTOP "UPGRADE_REQUIRES_MAINTENANCE: ResearchOS installation or retained data exists. This media has not changed it."
  SetErrorLevel 42
  Quit
FunctionEnd

Section "Reserved reviewed payload" SEC_PAYLOAD
  ; Defense in depth if the entry guard is altered in a later build.
  SetErrorLevel 43
  Abort "INSTALL_REQUIRES_TRANSACTION"
  SetOutPath "$PLUGINSDIR"
  File /oname=payload.zip "${ARCHIVE}"
  File /oname=payload-manifest.json "${MANIFEST}"
  File /oname=finalizer.exe "${FINALIZER}"
SectionEnd
