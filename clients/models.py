# clients/models.py
from django.db import models
from django.contrib.auth.models import User
from taxes.models import Pays
import logging

logger = logging.getLogger(__name__)


class Client(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')

    # Identité
    nom    = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)

    # Contact
    email = models.EmailField(blank=True)

    # Triée alphabétiquement par nom de pays (insensible aux accents).
    INDICATIF_CHOICES = [
        ('+27',   '🇿🇦 Afrique du Sud (+27)'),
        ('+213',  '🇩🇿 Algérie (+213)'),
        ('+49',   '🇩🇪 Allemagne (+49)'),
        ('+54',   '🇦🇷 Argentine (+54)'),
        ('+61',   '🇦🇺 Australie (+61)'),
        ('+880',  '🇧🇩 Bangladesh (+880)'),
        ('+32',   '🇧🇪 Belgique (+32)'),
        ('+229',  '🇧🇯 Bénin (+229)'),
        ('+55',   '🇧🇷 Brésil (+55)'),
        ('+226',  '🇧🇫 Burkina Faso (+226)'),
        ('+237',  '🇨🇲 Cameroun (+237)'),
        ('+1',    '🇨🇦 Canada / 🇺🇸 États-Unis (+1)'),
        ('+56',   '🇨🇱 Chili (+56)'),
        ('+86',   '🇨🇳 Chine (+86)'),
        ('+57',   '🇨🇴 Colombie (+57)'),
        ('+242',  '🇨🇬 Congo (+242)'),
        ('+82',   '🇰🇷 Corée du Sud (+82)'),
        ('+225',  '🇨🇮 Côte d\'Ivoire (+225)'),
        ('+45',   '🇩🇰 Danemark (+45)'),
        ('+20',   '🇪🇬 Égypte (+20)'),
        ('+34',   '🇪🇸 Espagne (+34)'),
        ('+251',  '🇪🇹 Éthiopie (+251)'),
        ('+358',  '🇫🇮 Finlande (+358)'),
        ('+33',   '🇫🇷 France (+33)'),
        ('+241',  '🇬🇦 Gabon (+241)'),
        ('+233',  '🇬🇭 Ghana (+233)'),
        ('+36',   '🇭🇺 Hongrie (+36)'),
        ('+91',   '🇮🇳 Inde (+91)'),
        ('+62',   '🇮🇩 Indonésie (+62)'),
        ('+39',   '🇮🇹 Italie (+39)'),
        ('+81',   '🇯🇵 Japon (+81)'),
        ('+254',  '🇰🇪 Kenya (+254)'),
        ('+60',   '🇲🇾 Malaisie (+60)'),
        ('+223',  '🇲🇱 Mali (+223)'),
        ('+212',  '🇲🇦 Maroc (+212)'),
        ('+52',   '🇲🇽 Mexique (+52)'),
        ('+977',  '🇳🇵 Népal (+977)'),
        ('+227',  '🇳🇪 Niger (+227)'),
        ('+234',  '🇳🇬 Nigeria (+234)'),
        ('+47',   '🇳🇴 Norvège (+47)'),
        ('+64',   '🇳🇿 Nouvelle-Zélande (+64)'),
        ('+256',  '🇺🇬 Ouganda (+256)'),
        ('+92',   '🇵🇰 Pakistan (+92)'),
        ('+31',   '🇳🇱 Pays-Bas (+31)'),
        ('+51',   '🇵🇪 Pérou (+51)'),
        ('+63',   '🇵🇭 Philippines (+63)'),
        ('+48',   '🇵🇱 Pologne (+48)'),
        ('+351',  '🇵🇹 Portugal (+351)'),
        ('+243',  '🇨🇩 RDC (+243)'),
        ('+420',  '🇨🇿 République Tchèque (+420)'),
        ('+44',   '🇬🇧 Royaume-Uni (+44)'),
        ('+7',    '🇷🇺 Russie (+7)'),
        ('+250',  '🇷🇼 Rwanda (+250)'),
        ('+221',  '🇸🇳 Sénégal (+221)'),
        ('+65',   '🇸🇬 Singapour (+65)'),
        ('+94',   '🇱🇰 Sri Lanka (+94)'),
        ('+46',   '🇸🇪 Suède (+46)'),
        ('+41',   '🇨🇭 Suisse (+41)'),
        ('+255',  '🇹🇿 Tanzanie (+255)'),
        ('+66',   '🇹🇭 Thaïlande (+66)'),
        ('+228',  '🇹🇬 Togo (+228)'),
        ('+216',  '🇹🇳 Tunisie (+216)'),
        ('+90',   '🇹🇷 Turquie (+90)'),
        ('+58',   '🇻🇪 Venezuela (+58)'),
        ('+84',   '🇻🇳 Vietnam (+84)'),
    ]

    indicatif = models.CharField(
        max_length=5,
        choices=INDICATIF_CHOICES,
        default='+226',
        verbose_name="Indicatif"
    )
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Numéro de téléphone")

    # ✅ Pays lié à la table Pays (devise + taxes automatiques)
    pays_obj = models.ForeignKey(
        Pays,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='clients',
        verbose_name="Pays"
    )

    # Adresse
    adresse     = models.TextField(blank=True)
    ville       = models.CharField(max_length=100, blank=True)
    code_postal = models.CharField(max_length=20, blank=True)
    province    = models.CharField(max_length=100, blank=True, verbose_name="Province / État / Région")

    # Entreprise
    entreprise = models.CharField(max_length=150, blank=True)

    # Logo client
    logo = models.ImageField(
        upload_to='clients/logos/',
        blank=True,
        null=True,
        verbose_name="Logo"
    )

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.entreprise:
            return f"{self.nom} {self.prenom} - {self.entreprise}"
        return f"{self.nom} {self.prenom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()

    @property
    def telephone_complet(self):
        if self.telephone:
            return f"{self.indicatif} {self.telephone}"
        return ""

    @property
    def devise(self):
        """Devise du client selon son pays"""
        if self.pays_obj:
            return self.pays_obj.devise_symbole
        return 'FCFA'

    @property
    def taux_tva(self):
        """
        ✅ CORRECTION : Calcule le taux total uniquement pour la province du client
        """
        if self.pays_obj:
            taxes = self.taxes_disponibles
            if taxes.exists():
                total = sum(taxe.taux for taxe in taxes)
                logger.debug(f"taux_tva pour {self.nom}: {total}% ({taxes.count()} taxes)")
                return total
        return 0

    @property
    def type_taxe_nom(self):
        """
        ✅ CORRECTION : Retourne uniquement les taxes de la province du client
        """
        if self.pays_obj:
            taxes = self.taxes_disponibles
            if taxes.exists():
                if taxes.count() == 1:
                    return taxes.first().code
                else:
                    result = " + ".join(taxe.code for taxe in taxes)
                    if len(result) > 50:
                        return f"{taxes.count()} taxes"
                    return result
        return 'TVA'

    @property
    def pays_nom(self):
        if self.pays_obj:
            return self.pays_obj.nom
        return ''
    
    @property
    def taxes_disponibles(self):
        """
        ✅ CORRECTION : Retourne les taxes disponibles selon la province du client
        """
        if not self.pays_obj:
            logger.debug(f"taxes_disponibles: {self.nom} - pas de pays")
            return []
        
        # Log pour diagnostic
        logger.info(f"taxes_disponibles pour {self.nom}:")
        logger.info(f"  - Pays: {self.pays_obj.nom} ({self.pays_obj.code})")
        logger.info(f"  - Province: '{self.province}'")
        
        # ✅ Filtrer STRICTEMENT par province
        if self.province and self.province.strip():
            # Si le client a une province, prendre uniquement les taxes de cette province
            taxes = self.pays_obj.taxes.filter(actif=True, province=self.province).order_by('ordre')
            logger.info(f"  - Taxes trouvées: {taxes.count()}")
            for t in taxes:
                logger.info(f"    - {t.code}: {t.taux}%")
            return taxes
        else:
            # Si pas de province, ne retourner AUCUNE taxe (pas de taxes par défaut)
            logger.warning(f"  - Client sans province -> aucune taxe")
            return self.pays_obj.taxes.none()

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'