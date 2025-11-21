Jeudi 20/11/2025
   - HB / HB AGE : Implementé : pas encore testé
   - Canal Teams : Le HTML :  KO non applicable
       ==> Adaptive Card : (JSON) : Test de rendu avec ;https://adaptivecards.microsoft.com/designer
  - By_business_line : encours d'implemenation
      Refacto faites : logique métiers : done
      Adpater le rapport (HTML)
      Le nombre de métier ? : faisabilite 
      FLOP : FLOP N 
  - INCIDENT 
      - token comme ressource Terraform.
      - Terraform devient responsable de créer, modifier et supprimer ce token
      - ancien token avait été créé en dehors de Terraform
      - Terraform voit qu’il doit créer un nouveau token
      - Terraform supprime l’ancien
