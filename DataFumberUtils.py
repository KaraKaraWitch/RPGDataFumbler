import orjson
import typer

app = typer.Typer()

@app.command()
def decode_json():
    print(orjson.loads(input("Enter encoded json>:")))

@app.command()
def encode_json():
    print(orjson.dumps(input("Enter decoded json>:")).decode())

if __name__ == "__main__":
    app()