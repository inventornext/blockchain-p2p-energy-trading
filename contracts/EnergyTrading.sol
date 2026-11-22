// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EnergyTrading {
    address public owner;
    uint public offerCount = 0;

    struct Offer {
        uint offerId;
        address prosumer;
        uint energyAmount; // in kWh
        uint pricePerKWh;  // in wei
        uint timestamp;    // hour of the day (0–23)
        uint remainingEnergy;
        bool isActive;
    }

    // Mapping from offerId to Offer
    mapping(uint => Offer) public offers;

    // Track energy purchased by each consumer
    mapping(address => uint) public energyPurchased;

    // Storage state per prosumer (in kWh)
    mapping(address => uint) public storageState;

    // Whether a prosumer has battery storage
    mapping(address => bool) public hasBattery;

    // Government rates (not used on-chain)
    uint public govBuyRate = 8 ether;   // 8 USD in wei
    uint public govSellRate = 20 ether; // 20 USD in wei

    event OfferCreated(uint offerId, address prosumer, uint energyAmount, uint pricePerKWh, uint timestamp);
    event EnergyBought(uint offerId, address consumer, uint amount, uint totalCost);
    event OfferDeactivated(uint offerId);
    event StorageUpdated(address prosumer, uint newStorage);

    constructor() {
        owner = msg.sender;
    }

    // Set battery storage availability (only once)
    function setBatteryStatus(bool _hasBattery) external {
        require(storageState[msg.sender] == 0, "Already initialized");
        hasBattery[msg.sender] = _hasBattery;
        if (_hasBattery) {
            storageState[msg.sender] = 10; // 10 kWh initial storage
            emit StorageUpdated(msg.sender, 10);
        }
    }

    // Prosumers create energy offers
    function createOffer(uint _energyAmount, uint _pricePerKWh, uint _hour) external {
        require(_energyAmount > 0, "Energy amount must be positive");
        require(_pricePerKWh >= 10 ether && _pricePerKWh <= 15 ether, "Price out of allowed range");

        if (hasBattery[msg.sender]) {
            require(storageState[msg.sender] >= _energyAmount, "Not enough stored energy");
            storageState[msg.sender] -= _energyAmount;
            emit StorageUpdated(msg.sender, storageState[msg.sender]);
        }

        offerCount++;
        offers[offerCount] = Offer({
            offerId: offerCount,
            prosumer: msg.sender,
            energyAmount: _energyAmount,
            pricePerKWh: _pricePerKWh,
            timestamp: _hour,
            remainingEnergy: _energyAmount,
            isActive: true
        });

        emit OfferCreated(offerCount, msg.sender, _energyAmount, _pricePerKWh, _hour);
    }

    // Consumers buy energy partially from available offers
    function buyEnergy(uint _offerId, uint _amount) external payable {
        Offer storage offer = offers[_offerId];
        require(offer.isActive, "Offer not active");
        require(_amount > 0 && _amount <= offer.remainingEnergy, "Invalid amount");

        uint cost = _amount * offer.pricePerKWh;
        require(msg.value >= cost, "Insufficient ETH sent");

        offer.remainingEnergy -= _amount;
        energyPurchased[msg.sender] += _amount;
        payable(offer.prosumer).transfer(cost);

        if (offer.remainingEnergy == 0) {
            offer.isActive = false;
            emit OfferDeactivated(_offerId);
        }

        emit EnergyBought(_offerId, msg.sender, _amount, cost);
    }

    // Government buys surplus (off-chain, only for recordkeeping)
    function recordGovBuy(address _prosumer, uint _amount) external {
        require(msg.sender == owner, "Only owner can record");
        // No ETH transfer – off-chain assumed
        emit EnergyBought(0, address(0), _amount, 0); // ID 0 used for govt tracking
    }

    // Government sells to customer (off-chain recorded)
    function recordGovSell(address _consumer, uint _amount) external {
        require(msg.sender == owner, "Only owner can record");
        energyPurchased[_consumer] += _amount;
        emit EnergyBought(0, _consumer, _amount, 0); // ID 0 used for govt tracking
    }

    // Function to check prosumer’s storage
    function getStorage(address _prosumer) external view returns (uint) {
        return storageState[_prosumer];
    }

    // Return all active offers
    function getActiveOffers() external view returns (Offer[] memory) {
        uint activeCount = 0;
        for (uint i = 1; i <= offerCount; i++) {
            if (offers[i].isActive) activeCount++;
        }

        Offer[] memory activeOffers = new Offer[](activeCount);
        uint index = 0;
        for (uint i = 1; i <= offerCount; i++) {
            if (offers[i].isActive) {
                activeOffers[index] = offers[i];
                index++;
            }
        }
        return activeOffers;
    }
}
