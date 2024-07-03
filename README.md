# Vtuber Chat Word Cloud

Generate Word Clouds from the YouTube Chat of any Vtuber

Requires a Holodex API key

## Instalation

```shell
pip install git+https://github.com/D-Brox/vtuber_chat_word_cloud
```

## Usage

```
$ vtuber_chat_word_cloud --help

 Usage: vtuber_chat_word_cloud [OPTIONS] NAME

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    name      TEXT  Vtuber name [default: None] [required]                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --image                         PATH     Image for the word cloud [default: None] [required]        │
│ *  --api-key                       TEXT     Holodex API key [default: None] [required]                 │
│    --average       --no-average             Average chat of all videos fetched [default: no-average]   │
│    --max-videos                    INTEGER  Max number of videos fetched [default: None]               │
│    --help                                   Show this message and exit.                                │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```