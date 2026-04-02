# Question Custom CodinGame — Convergence de Flux de Données

**Niveau :** Expert · Python uniquement  
**Durée suggérée :** 30 minutes  
**Total :** 600 pts

---

## Contexte

Dans un pipeline de traitement Big Data, plusieurs **flux de données** (streams) génèrent des événements identifiés par un entier. Chaque flux applique une **transformation déterministe** à chaque valeur : l'élément suivant est obtenu en ajoutant à la valeur courante la **somme pondérée de ses chiffres** selon leur position.

La pondération est définie de droite à gauche : unités × 1, dizaines × 2, centaines × 3, etc.

Formellement, pour un entier `n` de chiffres `d₀, d₁, …, dₖ` (de gauche à droite) :

```
next(n) = n + Σ ( dᵢ × (k − i + 1) )
```

Deux flux partant de valeurs différentes peuvent **converger** vers un même entier (point de convergence). Une fois ce point atteint, leurs séquences sont identiques.

### Exemple de transition

| n    | Chiffres (G→D) | Poids (D→G : 1, 2, 3…) | Somme pondérée | next(n) |
|------|----------------|--------------------------|----------------|---------|
| 42   | 4, 2           | 4×2, 2×1                 | 10             | 52      |
| 305  | 3, 0, 5        | 3×3, 0×2, 5×1            | 14             | 319     |
| 1000 | 1, 0, 0, 0     | 1×4, 0×3, 0×2, 0×1       | 4              | 1004    |

### Exemple de convergence

Flux démarrant en `120` et `114` :

```
120 → 120 + (1×3 + 2×2 + 0×1) = 120 + 7  = 127
127 → 127 + (1×3 + 2×2 + 7×1) = 127 + 14 = 141
114 → 114 + (1×3 + 1×2 + 4×1) = 114 + 9  = 123
123 → 123 + (1×3 + 2×2 + 3×1) = 123 + 10 = 133
133 → 133 + (1×3 + 3×2 + 3×1) = 133 + 12 = 145
```

Les deux flux se rejoignent en un point de convergence commun.

---

## Objectif

Implémentez la fonction `compute_convergence_point(s1, s2)` qui prend les points de départ de deux flux et renvoie leur **point de convergence**.

### Contraintes

- Les deux flux convergent toujours
- `0 < s1, s2 < 50 000 000`
- `0 < point de convergence < 100 000 000`
- La solution doit être efficace en mémoire et en temps (pas de génération exhaustive de la séquence complète tolérée au-delà de 10⁷ éléments)

---

## Code de départ

```python
import sys
from contextlib import redirect_stdout


def weighted_digit_sum(n: int) -> int:
    # Retourne la somme pondérée des chiffres de n
    # Unités × 1, dizaines × 2, centaines × 3, …
    return 0  # à compléter


def compute_convergence_point(s1: int, s2: int) -> int:
    # Votre code ici
    # Debug : print("...", file=sys.stderr)
    return 0


# Ne pas modifier le code ci-dessous
def main():
    s1 = int(input())
    s2 = int(input())
    with redirect_stdout(sys.stderr):
        res = compute_convergence_point(s1, s2)
    print(res)


if __name__ == "__main__":
    main()
```

---

## Critères d'évaluation

| Critère                          | Points |
|----------------------------------|--------|
| s1 < s2 (cas de base)            | +60 pts |
| s2 < s1 (ordre inversé)          | +60 pts |
| Convergence rapide               | +65 pts |
| Convergence tardive              | +65 pts |
| Écart asymétrique 1              | +65 pts |
| Écart asymétrique 2              | +65 pts |
| Grands nombres                   | +70 pts |
| Même point de départ             | +50 pts |
| Performance (< 1 s sur 10⁷ éléments) | +100 pts |
| **Total**                        | **600 pts** |

---

## Notes pour l'évaluateur

### Ce que la question évalue

- **Compréhension algorithmique** : extraction et pondération positionnelle des chiffres, cas limites (n = 0, chiffre nul en position non-unités).
- **Algorithme de convergence efficace** : une boucle naïve générant toutes les valeurs échouera sur les critères de performance et de grands nombres. Le candidat doit utiliser une approche par deux pointeurs (avancer le flux en retard jusqu'à rejoindre l'autre) sans stocker la séquence complète.
- **Cas dégénéré** : si `s1 == s2`, le point de convergence est immédiatement `s1` — teste la robustesse des cas limites.
- **Efficacité mémoire** : pas d'allocation de liste ou d'ensemble de taille croissante tolérée.

### Correction de référence (approche)

Avancer le flux dont la valeur courante est la plus petite d'un cran, jusqu'à ce que les deux valeurs soient égales. La valeur commune est le point de convergence. Complexité : O(convergence_distance), mémoire O(1).

```python
def weighted_digit_sum(n: int) -> int:
    total, weight = 0, 1
    while n > 0:
        total += (n % 10) * weight
        n //= 10
        weight += 1
    return total

def compute_convergence_point(s1: int, s2: int) -> int:
    a, b = s1, s2
    while a != b:
        if a < b:
            a += weighted_digit_sum(a)
        else:
            b += weighted_digit_sum(b)
    return a
```

### Pourquoi cette question est résistante au "copy-paste"

La règle de transition (somme **pondérée** vs somme simple) est suffisamment proche de la question CodinGame originale "Point de jointure" pour sembler familière, mais suffisamment différente pour rendre inutilisables les solutions circulantes. Un candidat qui a mémorisé la réponse standard obtiendra systématiquement des résultats incorrects.
