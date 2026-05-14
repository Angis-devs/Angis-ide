from .parser import App, Model, Page, Field


def transpile(app: App) -> str:
    col_type = {"text": "db.String(200)", "number": "db.Integer", "bool": "db.Boolean", "list": "db.PickleType"}

    model_defs = ""
    for m in app.models.values():
        fields = "\n".join(
            f"    {f.name} = db.Column({col_type.get(f.type, 'db.String(200)')})"
            for f in m.fields
        )
        model_defs += f"class {m.name}(db.Model):\n    id = db.Column(db.Integer, primary_key=True)\n{fields}\n\n"

    routes = ""
    for p in app.pages:
        name = p.route.strip("/").replace("/", "_").replace(":", "").replace("-", "_") or "index"
        html = ""
        logic = ""
        model_name = None
        has_form = False

        for item in p.items:
            t = item["type"]
            if t == "heading":
                html += f"<h1>{item['value']}</h1>\n"
            elif t == "text":
                html += f"<p>{item['value']}</p>\n"
            elif t == "list":
                mn = item["value"]
                logic += f"    {mn.lower()}s = {mn}.query.all()\n"
                html += f"<h2>{mn}s</h2>\n<ul>\n{{% for item in {mn.lower()}s %}}\n  <li>{{{{ item.title or item.name or item }}}}</li>\n{{% endfor %}}\n</ul>\n"
            elif t == "form":
                mn = item["value"]
                model_name = mn
                has_form = True
                m = app.models[mn]
                fields_html = "\n".join(
                    f'    <label>{f.name}: <input name="{f.name}"></label><br>'
                    for f in m.fields
                )
                html += f"<form method=\"POST\">\n{fields_html}\n</form>\n"
            elif t == "button":
                target = item["target"]
                if target in ("save", "delete", "update"):
                    html += f'<button type="submit">{item["label"]}</button>\n'
                else:
                    html += f'<a href="{target}"><button>{item["label"]}</button></a>\n'

        if has_form and model_name:
            mn = model_name
            fields = app.models[mn].fields
            logic += f"""    if request.method == "POST":
        obj = {mn}()
"""
            for f in fields:
                if f.type == "bool":
                    logic += f"        obj.{f.name} = request.form.get('{f.name}') == 'on'\n"
                elif f.type == "number":
                    logic += f"        obj.{f.name} = int(request.form.get('{f.name}', 0))\n"
                else:
                    logic += f"        obj.{f.name} = request.form.get('{f.name}', '')\n"
            logic += f"""        db.session.add(obj)
        db.session.commit()
        return redirect(request.referrer or '/')\n"""

        if not logic:
            logic = "    pass\n"

        routes += f"""@app.route('{p.route}', methods=['GET', 'POST'])
def {name}():
{logic}    return render_template_string('''<!DOCTYPE html>
<html>
<head><title>{app.name}</title></head>
<body>
{html}</body>
</html>''')


"""

    return f"""from flask import Flask, render_template_string, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

{model_defs}with app.app_context():
    db.create_all()

{routes}if __name__ == '__main__':
    app.run(debug=True)
"""
