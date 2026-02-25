Voici la **méthode “prod-ready” généralement utilisée à la BNP** (et plus largement dans les grandes DSI régulées) pour **packager une librairie Python interne** et la **publier/consommer via Artifactory**.

Je te la présente **de bout en bout**, avec les **bonnes pratiques attendues en production** (sécurité, versioning, CI/CD, traçabilité).

---

## 1️⃣ Structure standard de la librairie (obligatoire en prod)

On s’aligne sur les standards Python (PEP 517/518/621).

```text
my_lib/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── my_lib/
│       ├── __init__.py
│       └── core.py
├── tests/
│   └── test_core.py
└── .gitlab-ci.yml
```

📌 **Points clés BNP**

* `src/` layout obligatoire → évite les imports fantômes
* Tests unitaires **obligatoires**
* Licence explicite (souvent interne BNP)

---

## 2️⃣ `pyproject.toml` (format attendu)

👉 **Setuptools + wheel**, compatible Artifactory.

```toml
[build-system]
requires = ["setuptools>=65", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-lib"
version = "1.2.0"
description = "Librairie Python interne BNP"
authors = [{name = "BNP Paribas"}]
readme = "README.md"
requires-python = ">=3.9"

dependencies = [
    "pandas>=1.5,<3.0"
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

📌 **BNP best practice**

* Versions **figées ou bornées**
* Python version alignée avec l’OS de prod
* Pas de dépendance non référencée Artifactory

---

## 3️⃣ Build du package (wheel uniquement)

En prod BNP 👉 **pas de `setup.py install`**, **wheel uniquement**.

```bash
python -m build
```

Résultat :

```text
dist/
├── my_lib-1.2.0-py3-none-any.whl
└── my_lib-1.2.0.tar.gz
```

📌 En prod, **on déploie le `.whl`**, pas le `.tar.gz`.

---

## 4️⃣ Publication vers Artifactory (BNP standard)

BNP utilise **Artifactory** comme dépôt Python privé.

### Configuration `.pypirc`

```ini
[distutils]
index-servers = artifactory

[artifactory]
repository = https://artifactory.bnpparibas.com/artifactory/api/pypi/pypi-internal
username = __token__
password = ${ARTIFACTORY_TOKEN}
```

📌 Authentification :

* **Token technique** (jamais un compte perso)
* Stocké en **variable CI/CD sécurisée**

---

### Upload du package

```bash
python -m twine upload \
  --repository artifactory \
  dist/*.whl
```

✔ Version immuable
✔ Traçabilité complète
✔ Audit OK

---

## 5️⃣ CI/CD GitLab (schéma classique BNP)

```yaml
stages:
  - test
  - build
  - publish

test:
  stage: test
  script:
    - pip install -r requirements-dev.txt
    - pytest

build:
  stage: build
  script:
    - python -m build
  artifacts:
    paths:
      - dist/*.whl

publish:
  stage: publish
  script:
    - python -m twine upload dist/*.whl
  only:
    - tags
```

📌 **Règle BNP**

* Publication **uniquement via tag Git**
* Pas de push manuel en prod
* Build reproductible

---

## 6️⃣ Consommer la librairie dans un autre projet

### `pip.conf` (machine ou container)

```ini
[global]
index-url = https://artifactory.bnpparibas.com/artifactory/api/pypi/pypi-internal/simple
trusted-host = artifactory.bnpparibas.com
```

### `requirements.txt`

```text
my-lib==1.2.0
```

Installation :

```bash
pip install -r requirements.txt
```

📌 Aucun accès à PyPI public en prod BNP.

---

## 7️⃣ Versioning & règles prod BNP

| Élément            | Règle                   |
| ------------------ | ----------------------- |
| Version            | SemVer obligatoire      |
| Rétrocompatibilité | MAJOR only              |
| Dépendances        | Gelées                  |
| Wheel              | Unique source d’install |
| Publication        | CI uniquement           |
| Rollback           | Version précédente      |

---

## 8️⃣ Checklist “Prod Ready BNP” ✅

✔ Tests unitaires
✔ Wheel only
✔ Version immuable
✔ Token technique
✔ CI/CD
✔ Dépendances maîtrisées
✔ Artifactory interne

---

### Tu veux que je t’adapte ça :

* à **un contexte Data (Spark, Airflow, ML)** ?
* à **Docker / Kubernetes** ?
* à **une vraie policy BNP (DEV / UAT / PROD repos)** ?

Dis-moi ton contexte exact et je te fais le **template clé en main**.
