using UnityEngine;

public class EnemyAI : MonoBehaviour
{
    public Transform target;
    public float moveSpeed = 4f;
    public float stoppingDistance = 10f;
    public float shootRange = 20f;
    public float fireRate = 1f;
    
    private float health = 50f;
    private float lastShootTime;
    private Rigidbody rb;
    
    void Start()
    {
        rb = GetComponent<Rigidbody>();
        // Add a gun visual
        GameObject gun = GameObject.CreatePrimitive(PrimitiveType.Cube);
        gun.transform.SetParent(transform);
        gun.transform.localPosition = new Vector3(0.3f, 0.5f, 0.5f);
        gun.transform.localScale = new Vector3(0.2f, 0.2f, 0.8f);
    }
    
    void Update()
    {
        if (target == null) return;
        
        float distance = Vector3.Distance(transform.position, target.position);
        
        // Look at target
        Vector3 lookPos = target.position - transform.position;
        lookPos.y = 0;
        Quaternion rotation = Quaternion.LookRotation(lookPos);
        transform.rotation = Quaternion.Slerp(transform.rotation, rotation, Time.deltaTime * 5f);
        
        // Move towards player if too far
        if (distance > stoppingDistance)
        {
            Vector3 direction = (target.position - transform.position).normalized;
            rb.MovePosition(transform.position + direction * moveSpeed * Time.deltaTime);
        }
        
        // Shoot if in range
        if (distance < shootRange && Time.time > lastShootTime + (1f/fireRate))
        {
            Shoot();
        }
    }
    
    void Shoot()
    {
        lastShootTime = Time.time;
        
        RaycastHit hit;
        if (Physics.Raycast(transform.position + Vector3.up, transform.forward, out
