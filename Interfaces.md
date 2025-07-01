### Interfaces for Apex-Tactics
## Ursina implementation
With Ursina Python library, these Interfaces will remain fixed on screen while the 3D camera can freely move around the scene using a custom camera controller.
* In Ursina, se parent=camera.ui for screen-space Interface elements
* In Ursina, position coordinates range from -1 to 1 (screen space). Position each Interface such that the full panel is viewable within the screen space.
* In Ursina, set appropriate z values to control layering
* In Ursina, Interface elements won't be affected by 3D camera transformations
* The 3D world elements will mix with these fixed Interfaces.

## Character Panel
The user can show/hide this panel by pressing the "c" key.
The Character panel shows the Unit's physical, magical, spiritual stats and attack and defense values. It displays an overall power rating for the character.
# Name: The character's name.
# Class and Race: Class information is determined by the character's stats and abilities. There is not a selectable class. We will create a function that describes the character from the sum of their stats and abilities. Races have yet to be implemented. All characters will currently be call Terran.
# Power Level: We will create a function that assesses the character's overall power. For now this will be on a scale from 1 to 99.
# Paper doll: The Character panel shows the Unit model and eight slots (four to the left, four to the right) where specific item types can be equiped. These slots are:
1 Helmet
2 Armor
3 Gloves
4 Boots
5 Main-hand
6 Off-hand
7 Back
8 Talisman

## Inventory Panel
The user can show/hide this panel by pressing the "i" key.
The Inventory panel displays all items that the party has collectively. The Inventory panel is organized by item types, with separate tabs for each item type. Items that are currently equipped by a character are colored in greyscale values, instead of their normal colors. When mousing over these equipped items, the display shows the name of the character currently equipping that item.

## Talent Panel
The user can show/hide this panel by pressing the "t" key.
The Talent panel displays a tree of abilities available for assignment in the selected Unit. The tree goes down, with low level abilities at the top of the panel and higher level abilities towards the bottom.
The Talent panel contains 3 tabs for physical, magical, and spiritual talents.

## Party Panel
The user can show/hide this panel by pressing the "p" key.
The Party panel displays 5 tiles, which are like slots that can be used to select available saved Units to add to the current party. Below theses slots, the panel has an element that is a carosel of all characters available in the party. Below each unit is the unit's current status and power rating.
The top of the Party panel displays aggregate ratings for the Party's physical, magical, spiritual stats and attack and defense values. This should look identical to the display on the Character panel. The Party panel displays an overall power rating for the Party.

## Upgrade Panel
The user can show/hide this panel by pressing the "u" key. The upgrade panel is where the user can improve items along the tier list, from Base to Enhanced to Enchanted to Superpowered to Metapowered. Different items won from battle or purchased in shops can be used to perform the upgrades. The user can also select a character to attempt to destroy equippable items and recover the items used to perform the upgrades. If the player attempts to destroy a sentient item, there is a high chance that the item will attack the character, resulting in a 1-on-1 battle.
