# RPGDataFumbler

Because I hate MTool.

## Workflow

1. Map (Extracts text to a simplified json representation)
2. Export (Export to editable text)
3. Translate (do your bulk/first pass here)
4. Import (Import changes to a json format, tweak translations)
5. Apply (Creates a patched version. Test, etc)
6. Tweak, fix. (Redo Steps 3 to 5)

## Engines

- RPGMaker:
  - MV
  - MZ

## AutoFumbler (DataFumbler.Auto.py)

Supported "Translators"

- MTool (See notes below)
- Google
- DeepL
- MBart ("Offline" MBart Translation)

### Notes

- *MTool translations is not usable as-is when running scripts. Consider additionally using other translations in tandem or ditching Mtool entirely.*